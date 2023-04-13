import logging
from celery import shared_task

from datetime import datetime, timedelta

import mercantile
import pyproj
import os
from PIL import Image

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from rdwatch.models import SiteObservation

import io
from dataclasses import dataclass
from rdwatch.utils.worldview_processed.raster_tile import (
    get_worldview_processed_visual_tile,
)
from rdwatch.utils.worldview_processed.satellite_captures import get_captures, WorldViewProcessedCapture


@dataclass
class WebpTile:
    tile: mercantile.Tile
    timestamp: datetime
    image: Image.Image

logger = logging.getLogger(__name__)


@shared_task
def generate_video_task(site_observation_id: int) -> None:
    # Sample code for saving a file.
    # TODO: Update this function to actually generate a video
    site_observations = SiteObservation.objects.filter(siteeval=site_observation_id)
    logger.warning(f'Attempting to run generateVideo on site Observation: {site_observation_id}')
    web_mercator = pyproj.Proj("EPSG:3857")

    # Create a WGS 84 projection (SRS ID 4326)
    wgs84 = pyproj.Proj("EPSG:4326")
    for item in site_observations:
        mercator: tuple[float, float, float, float] = item.geom.extent
        lon_min, lat_min = pyproj.transform(web_mercator, wgs84, mercator[0], mercator[1])
        lon_max, lat_max = pyproj.transform(web_mercator, wgs84, mercator[2], mercator[3])
        bbox = [lat_min, lon_min, lat_max, lon_max]
        timestamp = item.timestamp
        constellation = item.constellation
        # We need to grab the image for this timerange and type
        if str(constellation) == 'WV':
            img = image(bbox, timestamp, worldview=True)
            if img is None:
                logger.warning(f'COULD NOT FIND ANY IMAGE FOR TIMESTAMP: {timestamp}')
                continue
            logger.warning(f'Retrieved Image with timestamp: {timestamp}')
            output = f'tile_image_{item.id}.jpg'
            img.save(output)
            with open(output, 'rb') as imageFile:
                item.video = File(imageFile, output)
                item.save()
                os.remove(output)


def get_closest_capture(
    bbox: tuple[float, float, float, float],
    timestamp: datetime,
):
    timebuffer = timedelta(days=1)

    captures = get_captures(timestamp, bbox, timebuffer)
    logger.warning(f'Captures: {len(captures)}')
    if not captures:
        return None
    closest_capture = min(captures, key=lambda band: abs(band.timestamp - timestamp))

    return closest_capture

def fetch_tile(
    capture: WorldViewProcessedCapture,
    tile: mercantile.Tile,
    timestamp: datetime,
    worldview: bool = False,
) -> WebpTile:
    try:
        buffer = get_worldview_processed_visual_tile(capture, tile.z, tile.x, tile.y)
        image = Image.open(io.BytesIO(buffer))
        return WebpTile(tile, timestamp, image)
    except:
        return None

def image(
    bbox: tuple[float, float, float, float],
    time: datetime,
    worldview: bool = False,
) -> Image.Image:
    # The max zoom will be different for lower resolution imagery
    # https://cogeotiff.github.io/rio-tiler/api/rio_tiler/io/cogeo/#get_zooms
    # This is for WorldView imagery
    zoom = 16 if worldview else 14

    webp_tiles: list[WebpTile] = []
    logger.warning(f'inside Image requesting')
    counter = 0
    capture = get_closest_capture(bbox, time)
    for tile in mercantile.tiles(*bbox, zoom):
        result = fetch_tile(capture, tile, time, worldview=worldview)
        if result is not None:
            webp_tiles.append(result)
        counter += 1
    if len(webp_tiles) == 0:
        return None
    logger.warning(f'Found {len(webp_tiles)} tiles!!')

    xmin = min(t.tile.x for t in webp_tiles)
    xmax = max(t.tile.x for t in webp_tiles)
    ymin = min(t.tile.y for t in webp_tiles)
    ymax = max(t.tile.y for t in webp_tiles)

    merged_width = ((xmax - xmin) + 1) * 512
    merged_height = ((ymax - ymin) + 1) * 512
    merged = Image.new('RGB', (merged_width, merged_height))
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
