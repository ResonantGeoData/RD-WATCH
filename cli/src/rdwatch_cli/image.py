from datetime import datetime

import aiohttp
import click
import mercantile

from rdwatch_cli.login import login
from rdwatch_cli.validators import validate_bbox, validate_timestamp


async def image(bbox: tuple[float, float, float, float], time: datetime) -> bytes:
    tile = mercantile.bounding_tile(*bbox)
    async with aiohttp.ClientSession(
        auth=login(),
        base_url="https://resonantgeodata.dev/",
    ) as client:
        async with client.get(
            f"api/satellite-image/tile/{tile.z}/{tile.x}/{tile.y}.webp",
            params={
                "constellation": "L8",
                "timestamp": time.isoformat(),
                "spectrum": "pan",
                "level": "1C",
            },
        ) as resp:
            return await resp.read()


@click.command()
@click.option("--bbox", nargs=4, type=click.UNPROCESSED, callback=validate_bbox)
@click.option("--time", type=click.UNPROCESSED, callback=validate_timestamp)
def image_cmd(bbox: tuple[float, float, float, float], time: datetime) -> None:
    """Retrieve an image for a bounding box at a specific time"""

    image(bbox, time)
