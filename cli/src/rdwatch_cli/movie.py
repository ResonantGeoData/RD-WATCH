from datetime import datetime

import click

from rdwatch_cli.login import login
from rdwatch_cli.validators import validate_bbox, validate_timestamps


def movie(
    bbox: tuple[float, float, float, float],
    time: tuple[datetime, ...],
) -> None:

    credentials = login()


@click.command()
@click.option("--bbox", nargs=4, type=click.UNPROCESSED, callback=validate_bbox)
@click.option(
    "--time",
    multiple=True,
    type=click.UNPROCESSED,
    callback=validate_timestamps,
)
def movie_cmd(
    bbox: tuple[float, float, float, float],
    time: tuple[datetime, ...],
) -> None:
    """Generate a movie for a bounding box at each timestamp"""

    movie(bbox, time)
