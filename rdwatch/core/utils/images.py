import io
import logging
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Literal
from urllib.error import URLError

from PIL import Image

from rdwatch.core.utils.capture import AbstractCapture
from rdwatch.core.utils.raster_tile import get_raster_bbox_from_reader
from rdwatch.core.utils.satellite_bands import get_bands
from rdwatch.core.utils.worldview_nitf.raster_tile import get_worldview_nitf_bbox
from rdwatch.core.utils.worldview_nitf.satellite_captures import (
    get_captures as get_worldview_nitf_captures,
)
from rdwatch.core.utils.worldview_processed.raster_tile import (
    get_worldview_processed_visual_bbox,
)
from rdwatch.core.utils.worldview_processed.satellite_captures import (
    get_captures as get_worldview_captures,
)

logger = logging.getLogger(__name__)


@contextmanager
def ignore_pillow_filesize_limits() -> Generator[None, None, None]:
    """
    Large image files can cause Pillow to raise a DecompressionBombError.
    This context manager temporarily disables the Pillow limit on the maximum image
    size, use it when the image is trusted but may be too large.
    """
    original_max_image_pixels = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = None
    yield
    Image.MAX_IMAGE_PIXELS = original_max_image_pixels


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


def get_max_bbox(
    bbox: tuple[float, float, float, float], maxbbox: tuple[float, float, float, float]
):
    newbbox = [
        min(bbox[0], maxbbox[0]),
        min(bbox[1], maxbbox[1]),
        max(bbox[2], maxbbox[2]),
        max(bbox[3], maxbbox[3]),
    ]
    return newbbox


def get_percent_black_pixels(bytes: bytes):
    with ignore_pillow_filesize_limits():
        img = Image.open(io.BytesIO(bytes))

    # determine the size of the image
    width, height = img.size

    # get the pixel data of the image
    pixels = img.load()

    # count the number of black pixels in the image
    num_black_pixels = 0
    for x in range(width):
        for y in range(height):
            if pixels[x, y] == (0, 0, 0):
                num_black_pixels += 1

    # calculate the percentage of black pixels in the image
    percent_black_pixels = (num_black_pixels / (width * height)) * 100
    return percent_black_pixels


def get_range_captures(
    bbox: tuple[float, float, float, float],
    timestamp: datetime,
    constellation: str,
    timebuffer: timedelta,
    worldView: Literal['cog', 'nitf'] | None,
) -> list[AbstractCapture]:
    if constellation == 'WV' and worldView == 'cog':
        captures = get_worldview_captures(timestamp, bbox, timebuffer)
    elif constellation == 'WV' and worldView == 'nitf':
        captures = get_worldview_nitf_captures(timestamp, bbox, timebuffer)
    else:
        captures = list(get_bands(constellation, timestamp, bbox, timebuffer))

        # Filter bands by requested processing level and spectrum
        tempCaptures = []
        for band in captures:
            if band.level.slug == '2A' and band.spectrum.slug == 'visual':
                tempCaptures.append(band)
        captures = tempCaptures

    return captures


def fetch_boundbox_image(
    bbox: tuple[float, float, float, float],
    timestamp: datetime,
    constellation: str,
    worldView: Literal['cog', 'nitf'] | None = None,
    scale: Literal['default', 'bits'] | list[int] = 'bits',
):
    timebuffer = timedelta(days=1)
    try:
        captures = get_range_captures(
            bbox,
            timestamp,
            constellation,
            timebuffer,
            worldView,
        )
    except URLError as e:
        logger.warning('Failed to get range capture because of URLError')
        logger.warning(e)
        return None

    if len(captures) == 0:
        return None
    closest_capture = min(captures, key=lambda band: abs(band.timestamp - timestamp))
    if worldView == 'cog' and constellation == 'WV':
        bytes = get_worldview_processed_visual_bbox(closest_capture, bbox, 'PNG', scale)
    elif worldView == 'nitf' and constellation == 'WV':
        bytes = get_worldview_nitf_bbox(closest_capture, bbox, 'PNG', scale)
    else:
        with closest_capture.open_reader() as reader:
            bytes = get_raster_bbox_from_reader(reader, bbox, 'PNG', scale)
    return {
        'bytes': bytes,
        'cloudcover': closest_capture.cloudcover,
        'timestamp': closest_capture.timestamp,
        'uris': closest_capture.uris,
    }
