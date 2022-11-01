import asyncio
from datetime import datetime
from pathlib import Path

import aiohttp
import click

# register pillow plugin
import pillow_avif  # type: ignore # noqa
from PIL import Image

from rdwatch_cli.exceptions import ImageNotFound, ServerError
from rdwatch_cli.image import image
from rdwatch_cli.login import login
from rdwatch_cli.utils import get_http_client
from rdwatch_cli.validators import validate_bbox


async def try_to_fetch_image(
    bbox: tuple[float, float, float, float],
    time: datetime,
    client: aiohttp.ClientSession | None = None,
    worldview: bool = False,
):
    try:
        return await image(
            bbox,
            time,
            client=client,
            worldview=worldview,
        )
    except ServerError:
        click.echo(f"Skipping {time} due to server error (malformed raw image?)")
        return None


async def movie(
    bbox: tuple[float, float, float, float],
    start_time: datetime,
    end_time: datetime,
    worldview: bool = False,
) -> list[Image.Image]:

    login()

    url = (
        "/api/satellite-image/visual-timestamps"
        if worldview
        else "/api/satellite-image/timestamps"
    )

    params = (
        {
            "start_timestamp": datetime.isoformat(start_time),
            "end_timestamp": datetime.isoformat(end_time),
            "bbox": ",".join(str(x) for x in bbox),
        }
        if worldview
        else {
            "constellation": "S2",
            "start_timestamp": datetime.isoformat(start_time),
            "end_timestamp": datetime.isoformat(end_time),
            "spectrum": "visual",
            "level": "2A",
            "bbox": ",".join(str(x) for x in bbox),
        }
    )

    async with get_http_client() as client:
        resp = await client.get(url, params=params)
        timestamps = await resp.json()

        if not timestamps:
            raise ImageNotFound()
        if not resp.ok:
            raise ServerError()

        return await asyncio.gather(
            *(
                try_to_fetch_image(
                    bbox,
                    datetime.fromisoformat(timestamp),
                    client=client,
                    worldview=worldview,
                )
                for timestamp in timestamps
            )
        )


@click.command()
@click.option("--output", type=Path)
@click.option("--bbox", nargs=4, type=click.UNPROCESSED, callback=validate_bbox)
@click.option("--start-time", type=click.DateTime())
@click.option("--end-time", type=click.DateTime())
@click.option("--worldview", type=bool)
def movie_cmd(
    output: Path,
    bbox: tuple[float, float, float, float],
    start_time: datetime,
    end_time: datetime,
    worldview: bool = False,
) -> None:
    """Generate a movie for a bounding box at each timestamp"""
    try:
        imgs = [
            img
            for img in asyncio.run(
                movie(bbox, start_time, end_time, worldview=worldview)
            )
            if img
        ]
        imgs[0].save(output, save_all=True, append_images=imgs)
    except ImageNotFound:
        raise click.ClickException("No image found for the given bounding box and time")
    except ServerError:
        raise click.ClickException("Server down (try again later)")
