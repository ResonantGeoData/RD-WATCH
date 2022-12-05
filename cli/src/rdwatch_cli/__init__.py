import asyncio
from datetime import datetime
from functools import wraps
from pathlib import Path

import aiohttp
import click

from rdwatch_cli import api
from rdwatch_cli.config import get_credentials, set_credentials
from rdwatch_cli.exceptions import ImageNotFound, ServerError
from rdwatch_cli.validators import validate_bbox, validate_timestamp


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


cli.add_command(login_cmd, name="login")
cli.add_command(image_cmd, name="image")
cli.add_command(movie_cmd, name="movie")
