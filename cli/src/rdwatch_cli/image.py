import asyncio
import io
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import aiohttp
import click
import mercantile
from PIL import Image

from rdwatch_cli.exceptions import ImageNotFound, ServerError
from rdwatch_cli.utils import get_http_client
from rdwatch_cli.validators import validate_bbox, validate_timestamp


@dataclass
class WebpTile:
    tile: mercantile.Tile
    timestamp: datetime
    image: Image.Image


async def fetch_tile(
    client: aiohttp.ClientSession,
    time: datetime,
    tile: mercantile.Tile,
    worldview: bool = False,
) -> WebpTile:

    url = (
        f"/api/satellite-image/visual-tile/{tile.z}/{tile.x}/{tile.y}.webp"
        if worldview
        else f"/api/satellite-image/tile/{tile.z}/{tile.x}/{tile.y}.webp"
    )

    params = (
        {"timestamp": time.isoformat()}
        if worldview
        else {
            "constellation": "S2",
            "timestamp": time.isoformat(),
            "spectrum": "visual",
            "level": "2A",
        }
    )

    async with client.get(url, params=params) as resp:
        buffer = await resp.read()
        if resp.status == 404:
            raise ImageNotFound()
        elif not resp.ok:
            raise ServerError()
        image = Image.open(io.BytesIO(buffer))
        return WebpTile(tile, time, image)


async def image(
    bbox: tuple[float, float, float, float],
    time: datetime,
    client: aiohttp.ClientSession | None = None,
    worldview: bool = False,
) -> Image.Image:
    # The max zoom will be different for lower resolution imagery
    # https://cogeotiff.github.io/rio-tiler/api/rio_tiler/io/cogeo/#get_zooms
    # This is for WorldView imagery
    zoom = 18 if worldview else 14

    webp_tiles: list[WebpTile]
    if client is None:
        async with get_http_client() as client:
            webp_tiles = await asyncio.gather(
                *(
                    fetch_tile(client, time, tile)
                    for tile in mercantile.tiles(*bbox, zoom)
                )
            )
    else:
        webp_tiles = await asyncio.gather(
            *(
                fetch_tile(client, time, tile, worldview=worldview)
                for tile in mercantile.tiles(*bbox, zoom)
            )
        )

    xmin = min(t.tile.x for t in webp_tiles)
    xmax = max(t.tile.x for t in webp_tiles)
    ymin = min(t.tile.y for t in webp_tiles)
    ymax = max(t.tile.y for t in webp_tiles)

    merged_width = ((xmax - xmin) + 1) * 512
    merged_height = ((ymax - ymin) + 1) * 512
    merged = Image.new("RGB", (merged_width, merged_height))
    for tile in webp_tiles:
        x = (tile.tile.x - xmin) * 512
        y = (tile.tile.y - ymin) * 512
        merged.paste(tile.image, (x, y))

    tile_bboxes = [mercantile.bounds(t.tile) for t in webp_tiles]
    bbox_xmin = min(b.west for b in tile_bboxes)
    bbox_xmax = max(b.east for b in tile_bboxes)
    bbox_ymin = min(b.south for b in tile_bboxes)
    bbox_ymax = max(b.north for b in tile_bboxes)

    xscale = merged_width / (bbox_xmax - bbox_xmin)
    yscale = merged_height / (bbox_ymax - bbox_ymin)

    crop_left = (bbox[0] - bbox_xmin) * xscale
    crop_right = (bbox[2] - bbox_xmin) * xscale
    crop_top = (bbox[3] - bbox_ymax) * -yscale
    crop_bottom = (bbox[1] - bbox_ymax) * -yscale
    crop = merged.crop((crop_left, crop_top, crop_right, crop_bottom))

    return crop


@click.command()
@click.option("--output", type=Path)
@click.option("--bbox", nargs=4, type=click.UNPROCESSED, callback=validate_bbox)
@click.option("--time", type=click.UNPROCESSED, callback=validate_timestamp)
@click.option("--worldview", type=bool)
def image_cmd(
    output: Path,
    bbox: tuple[float, float, float, float],
    time: datetime,
    worldview: bool = False,
) -> None:
    """Retrieve an image for a bounding box at a specific time"""
    try:
        img = asyncio.run(image(bbox, time, worldview=worldview))
        img.save(output)
    except ImageNotFound:
        raise click.ClickException("No image found for the given bounding box and time")
    except ServerError:
        raise click.ClickException("Server down (try again later)")
