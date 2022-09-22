import asyncio
from datetime import datetime
from pathlib import Path

import click

# register pillow plugin
import pillow_avif  # type: ignore # noqa
from PIL import Image

from rdwatch_cli.image import image
from rdwatch_cli.login import login
from rdwatch_cli.validators import validate_bbox, validate_timestamps


async def movie(
    bbox: tuple[float, float, float, float],
    time: tuple[datetime, ...],
) -> list[Image.Image]:

    login()

    times = list(time)
    times.sort()
    images: list[Image.Image] = await asyncio.gather(*(image(bbox, t) for t in times))
    return images


@click.command()
@click.option("--output", type=Path)
@click.option("--bbox", nargs=4, type=click.UNPROCESSED, callback=validate_bbox)
@click.option(
    "--time",
    multiple=True,
    type=click.UNPROCESSED,
    callback=validate_timestamps,
)
def movie_cmd(
    output: Path,
    bbox: tuple[float, float, float, float],
    time: tuple[datetime, ...],
) -> None:
    """Generate a movie for a bounding box at each timestamp"""

    imgs = asyncio.run(movie(bbox, time))
    imgs[0].save(output, save_all=True, append_images=imgs[1:])
