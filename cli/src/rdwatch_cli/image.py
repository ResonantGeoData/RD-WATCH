import asyncio
import io
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import aiohttp
import click
import mercantile
from PIL import Image

from rdwatch_cli.login import login
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
) -> WebpTile:
    async with client.get(
        f"/api/satellite-image/tile/{tile.z}/{tile.x}/{tile.y}.webp",
        params={
            "constellation": "S2",
            "timestamp": time.isoformat(),
            "spectrum": "visual",
            "level": "2A",
        },
    ) as resp:
        buffer = await resp.read()
        image = Image.open(io.BytesIO(buffer))
        return WebpTile(tile, time, image)


async def image(bbox: tuple[float, float, float, float], time: datetime) -> Image.Image:
    # The max zoom will be different for higher resolution imagery
    # https://cogeotiff.github.io/rio-tiler/api/rio_tiler/io/cogeo/#get_zooms
    # This is for Sentinel-2
    zoom = 14

    async with aiohttp.ClientSession(
        auth=login(),
        base_url="https://resonantgeodata.dev",
    ) as client:
        webp_tiles: list[WebpTile] = await asyncio.gather(
            *(fetch_tile(client, time, tile) for tile in mercantile.tiles(*bbox, zoom))
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
    crop_top = (bbox[1] - bbox_ymin) * yscale
    crop_bottom = (bbox[3] - bbox_ymin) * yscale
    crop = merged.crop((crop_left, crop_top, crop_right, crop_bottom))

    return crop


@click.command()
@click.option("--output", type=Path)
@click.option("--bbox", nargs=4, type=click.UNPROCESSED, callback=validate_bbox)
@click.option("--time", type=click.UNPROCESSED, callback=validate_timestamp)
def image_cmd(
    output: Path,
    bbox: tuple[float, float, float, float],
    time: datetime,
) -> None:
    """Retrieve an image for a bounding box at a specific time"""

    img = asyncio.run(image(bbox, time))
    img.save(output)
