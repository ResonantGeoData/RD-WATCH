import io
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from celery import shared_task


from pyproj import Transformer

from django.core.files import File
from PIL import Image
from rdwatch.models import SiteObservation, SiteImage
from rdwatch.utils.raster_tile import get_raster_tile_bbox
from rdwatch.utils.satellite_bands import get_bands
from rdwatch.utils.worldview_processed.raster_tile import (
    get_worldview_processed_visual_bbox,
    get_worldview_processed_visual_tile,
)
from rdwatch.utils.worldview_processed.satellite_captures import (
    WorldViewProcessedCapture,
)
from rdwatch.utils.worldview_processed.satellite_captures import (
    get_captures as get_worldview_captures,
)

logger = logging.getLogger(__name__)

@dataclass
class WebpTile:
    tile: mercantile.Tile
    timestamp: datetime
    image: Image.Image

def scale_bbox(bbox: tuple[float, float, float, float], scale_factor: float):
    xmin, ymin, xmax, ymax = bbox
    width = xmax - xmin
    height = ymax - ymin
    new_width = width * scale_factor
    new_height = height * scale_factor
    new_xmin = xmin - ((new_width - width) / 2)
    new_ymin = ymin - ((new_height - height) / 2)
    new_xmax = xmax + ((new_width - width) / 2)
    new_ymax = ymax + ((new_height - height) / 2)
    scaled_bbox = [new_xmin, new_ymin, new_xmax, new_ymax]
    return scaled_bbox

def get_closest_capture(
    bbox: tuple[float, float, float, float],
    timestamp: datetime,
    constellation: str,
    worldView=False,
):
    timebuffer = timedelta(days=1)
    captures = None
    if worldView:
        captures = get_worldview_captures(timestamp, bbox, timebuffer)
    else:
        logger.warning(
            f'Getting capture constellation: {constellation} \
            timestmap: {timestamp} bbox: {bbox}'
        )
        captures = list(get_bands(constellation, timestamp, bbox, timebuffer))

        # Filter bands by requested processing level and spectrum
        tempCaptures = []
        for band in captures:
            if band.level.slug == '2A' and band.spectrum.slug == 'visual':
                tempCaptures.append(band)
        captures = tempCaptures
    logger.warning(f'Captures: {len(captures)}')
    if not captures:
        return None
    closest_capture = min(captures, key=lambda band: abs(band.timestamp - timestamp))

    return closest_capture

def fetch_boundbox_image(
    bbox: tuple[float, float, float, float],
    timestamp: datetime,
    constellation: str,
    worldView=False,
):
    capture = get_closest_capture(bbox, timestamp, constellation, worldView)
    logger.warning(f'Closest Capture is: {capture}')
    if capture is None:
        return None
    bytes = None
    if worldView:
        bytes = get_worldview_processed_visual_bbox(capture, bbox)
    else:
        bytes = get_worldview_processed_visual_tile(capture.uri, bbox)
    return bytes

@shared_task
def get_siteobservations_images(site_observation_id: int, baseConstellation='WV') -> None:
    site_observations = SiteObservation.objects.filter(siteeval=site_observation_id)
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326")
    for observation in site_observations:
        mercator: tuple[float, float, float, float] = observation.geom.extent
        tempbox = transformer.transform_bounds(
            mercator[0], mercator[1], mercator[2], mercator[3]
        )
        bbox = [tempbox[1], tempbox[0], tempbox[3], tempbox[2]]
        bbox = scale_bbox(bbox, 1.2)
        timestamp = observation.timestamp
        constellation = observation.constellation
        # We need to grab the image for this timerange and type
        logger.warning(
            f'Comparing site constellation: {constellation} \
                to test constellation: {baseConstellation}'
        )
        if str(constellation) == baseConstellation:
            logger.warning(f'Trying to retrieve for constellation: {constellation}')
            bytes = fetch_boundbox_image(
                bbox, timestamp, constellation, baseConstellation == 'WV'
            )
            # img = image(bbox, timestamp, worldview=True) # Old way
            if bytes is None:
                logger.warning(f'COULD NOT FIND ANY IMAGE FOR TIMESTAMP: {timestamp}')
                continue
            logger.warning(f'Retrieved Image with timestamp: {timestamp}')
            output = f'tile_image_{observation.id}.jpg'
            with open(output, "wb") as f:
                f.write(bytes)
            with open(output, 'rb') as imageFile:
                image = File(imageFile, output)
                SiteImage.objects.create(
                    siteeval=observation.siteeval,
                    siteobs=observation.id,
                    timestamp=observation.timestamp,
                    image=image,
                    source=baseConstellation,
                )
                os.remove(output)
