import asyncio
from datetime import datetime
from pathlib import Path

import aiohttp
import click
import mercantile

# register pillow plugin
import pillow_avif  # type: ignore # noqa
from PIL import Image

from rdwatch_cli.image import image
from rdwatch_cli.login import login
from rdwatch_cli.validators import validate_bbox


async def movie(
    bbox: tuple[float, float, float, float],
    start_time: datetime,
    end_time: datetime,
) -> list[Image.Image]:
    # The max zoom will be different for higher resolution imagery
    # https://cogeotiff.github.io/rio-tiler/api/rio_tiler/io/cogeo/#get_zooms
    # This is for Sentinel-2
    zoom = 14

    tile = next(mercantile.tiles(*bbox, zoom))

    login()

    # Get images available from
    async with aiohttp.ClientSession(
        auth=login(),
        base_url="https://resonantgeodata.dev",
    ) as client:
        resp = await client.get(
            f"/api/satellite-image/{tile.z}/{tile.x}/{tile.y}",
            params={
                "constellation": "S2",
                "start_timestamp": datetime.isoformat(start_time),
                "end_timestamp": datetime.isoformat(end_time),
                "spectrum": "blue",  # TODO: change to make it visual
                "level": "2A",
            },
        )
        images = await resp.json()

    return await asyncio.gather(
        *(image(bbox, datetime.fromisoformat(im["timestamp"])) for im in images)
    )


@click.command()
@click.option("--output", type=Path)
@click.option("--bbox", nargs=4, type=click.UNPROCESSED, callback=validate_bbox)
@click.option(
    "--start-time",
    type=click.DateTime(),
)
@click.option(
    "--end-time",
    type=click.DateTime(),
)
def movie_cmd(
    output: Path,
    bbox: tuple[float, float, float, float],
    start_time: datetime,
    end_time: datetime,
) -> None:
    """Generate a movie for a bounding box at each timestamp"""
    imgs = asyncio.run(movie(bbox, start_time, end_time))
    imgs[0].save(output, save_all=True, append_images=imgs[1:])
