import asyncio
import io
from dataclasses import dataclass
from datetime import datetime

import aiohttp
import mercantile
from PIL import Image

from rdwatch_cli.exceptions import ImageNotFound, ServerError


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

    params = {"timestamp": datetime.isoformat(time)}
    if not worldview:
        params["constellation"] = "S2"
        params["spectrum"] = "visual"
        params["level"] = "2A"

    async with client.get(url, params=params) as resp:
        buffer = await resp.read()
        if resp.status == 404:
            raise ImageNotFound()
        elif not resp.ok:
            raise ServerError()
        image = Image.open(io.BytesIO(buffer))
        return WebpTile(tile, time, image)


async def image(
    client: aiohttp.ClientSession,
    bbox: tuple[float, float, float, float],
    time: datetime,
    worldview: bool = False,
) -> Image.Image:
    # The max zoom will be different for lower resolution imagery
    # https://cogeotiff.github.io/rio-tiler/api/rio_tiler/io/cogeo/#get_zooms
    # This is for WorldView imagery
    zoom = 18 if worldview else 14

    webp_tiles: list[WebpTile]
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
