import asyncio
from datetime import datetime
from functools import wraps
from pathlib import Path

import aiohttp
import click

from rdwatch_cli import api
from rdwatch_cli.config import get_credentials, set_credentials
from rdwatch_cli.exceptions import ImageNotFound, ServerError
from rdwatch_cli.validators import validate_bbox


def _login():
    """Set HTTP Basic Auth credentials"""

    username = click.prompt("Username", type=str)
    password = click.prompt(
        "Password",
        type=str,
        confirmation_prompt=True,
        hide_input=True,
    )
    set_credentials(username, password)
    return get_credentials()


def _get_http_client(host: str) -> aiohttp.ClientSession:
    """Get an HTTP client for the given host.

    Will prompt for login credentials if they are not already set.
    """

    auth = None
    if host == "https://resonantgeodata.dev":
        auth = get_credentials() or _login()

    return aiohttp.ClientSession(
        auth=auth,
        base_url=host,
        timeout=aiohttp.ClientTimeout(
            sock_read=120,
            connect=None,
            sock_connect=None,
            total=None,
        ),
        connector=aiohttp.TCPConnector(limit=30),
    )


def _coroutine(f):
    """Run a click command as a coroutine."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group()
def cli():
    ...


@cli.command()
def login():
    """Set HTTP Basic Auth credentials"""
    _login()


@cli.command()
@click.option(
    "--host",
    type=str,
    default="https://resonantgeodata.dev",
    show_default=True,
    help="Hostname of the RD-Watch instance to use",
)
@click.option("--output", type=Path, help="Output file path")
@click.option(
    "--bbox",
    nargs=4,
    type=click.UNPROCESSED,
    callback=validate_bbox,
    help="Bounding box (min-x min-y max-x max-y)",
)
@click.option(
    "--time",
    type=click.DateTime(),
    help="Time near satellite capture",
)
@click.option(
    "--worldview",
    is_flag=True,
    help="Use WorldView satellite imagery instead of Sentinel-2",
)
@_coroutine
async def image(
    host: str,
    output: Path,
    bbox: tuple[float, float, float, float],
    time: datetime,
    worldview: bool,
) -> None:
    """Retrieve an image for a bounding box at a specific time"""
    async with _get_http_client(host) as client:
        try:
            img = await api.image(client, bbox, time, worldview=worldview)
            img.save(output)
        except ImageNotFound:
            raise click.ClickException(
                "No image found for the given bounding box and time"
            )
        except ServerError:
            raise click.ClickException("Server down (try again later)")


@cli.command()
@click.option(
    "--host",
    type=str,
    default="https://resonantgeodata.dev",
    show_default=True,
    help="Hostname of the RD-Watch instance to use",
)
@click.option("--output", type=Path, help="Output file path")
@click.option(
    "--bbox",
    nargs=4,
    type=click.UNPROCESSED,
    callback=validate_bbox,
    help="Bounding box (min-x min-y max-x max-y)",
)
@click.option(
    "--start-time",
    type=click.DateTime(),
    help="Time near beginning of satellite capture",
)
@click.option(
    "--end-time",
    type=click.DateTime(),
    help="Time near end of satellite capture",
)
@click.option(
    "--worldview",
    is_flag=True,
    help="Use WorldView satellite imagery instead of Sentinel-2",
)
@_coroutine
async def movie(
    host: str,
    output: Path,
    bbox: tuple[float, float, float, float],
    start_time: datetime,
    end_time: datetime,
    worldview: bool,
) -> None:
    """Generate a movie for a bounding box at each timestamp"""
    async with _get_http_client(host) as client:
        try:
            imgs = [
                img
                for img in await api.movie(
                    client,
                    bbox,
                    start_time,
                    end_time,
                    worldview=worldview,
                )
                if img
            ]
            imgs[0].save(output, save_all=True, append_images=imgs)
        except ImageNotFound:
            raise click.ClickException(
                "No image found for the given bounding box and time"
            )
        except ServerError:
            raise click.ClickException("Server down (try again later)")
