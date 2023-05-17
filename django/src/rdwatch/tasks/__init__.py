import io
import logging
from datetime import datetime, timedelta

from celery import shared_task
from PIL import Image
from pyproj import Transformer

from django.core.files import File

from rdwatch.models import SatelliteFetching, SiteImage, SiteObservation
from rdwatch.utils.raster_tile import get_raster_bbox
from rdwatch.utils.satellite_bands import get_bands
from rdwatch.utils.worldview_processed.raster_tile import (
    get_worldview_processed_visual_bbox,
)
from rdwatch.utils.worldview_processed.satellite_captures import (
    get_captures as get_worldview_captures,
)

logger = logging.getLogger(__name__)


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
        max(bbox[2], maxbbox[3]),
        max(bbox[2], maxbbox[3]),
    ]
    return newbbox


def get_percent_black_pixels(bytes: bytes):
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
    worldView=False,
):
    if worldView:
        captures = get_worldview_captures(timestamp, bbox, timebuffer)
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
    worldView=False,
):
    timebuffer = timedelta(days=1)
    captures = get_range_captures(bbox, timestamp, constellation, timebuffer, worldView)
    if len(captures) == 0:
        return None
    closest_capture = min(captures, key=lambda band: abs(band.timestamp - timestamp))
    if worldView:
        bytes = get_worldview_processed_visual_bbox(closest_capture, bbox)
    else:
        bytes = get_raster_bbox(closest_capture.uri, bbox)
    return {
        'bytes': bytes,
        'cloudcover': closest_capture.cloudcover,
        'timestamp': closest_capture.timestamp,
    }


@shared_task
def get_siteobservations_images(
    site_eval_id: int, baseConstellation='WV', force=False
) -> None:
    site_observations = SiteObservation.objects.filter(siteeval=site_eval_id)
    transformer = Transformer.from_crs('EPSG:3857', 'EPSG:4326')
    found_timestamps = {}
    min_time = datetime.max
    max_time = datetime.min
    max_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]
    matchConstellation = ''
    baseSiteEval = None
    # First we gather all images that match observations
    for observation in site_observations.iterator():
        min_time = min(min_time, observation.timestamp)
        max_time = max(max_time, observation.timestamp)
        mercator: tuple[float, float, float, float] = observation.geom.extent
        tempbox = transformer.transform_bounds(
            mercator[0], mercator[1], mercator[2], mercator[3]
        )
        bbox = [tempbox[1], tempbox[0], tempbox[3], tempbox[2]]
        bbox = scale_bbox(bbox, 1.2)
        max_bbox = get_max_bbox(bbox, max_bbox)
        timestamp = observation.timestamp
        constellation = observation.constellation
        # We need to grab the image for this timerange and type
        if str(constellation) == baseConstellation:
            baseSiteEval = observation.siteeval
            matchConstellation = constellation
            found = SiteImage.objects.filter(
                siteeval=observation.siteeval,
                siteobs=observation,
                timestamp=observation.timestamp,
                source=baseConstellation,
            )
            if found.exists() and not force:
                found_timestamps[observation.timestamp] = True
                continue
            results = fetch_boundbox_image(
                bbox, timestamp, constellation, baseConstellation == 'WV'
            )
            if results is None:
                logger.warning(f'COULD NOT FIND ANY IMAGE FOR TIMESTAMP: {timestamp}')
                continue
            bytes = results['bytes']
            percent_black = get_percent_black_pixels(bytes)
            cloudcover = results['cloudcover']
            found_timestamp = results['timestamp']
            if bytes is None:
                logger.warning(f'COULD NOT FIND ANY IMAGE FOR TIMESTAMP: {timestamp}')
                continue
            found_timestamps[found_timestamp] = True
            # logger.warning(f'Retrieved Image with timestamp: {timestamp}')
            output = f'tile_image_{observation.id}.jpg'
            image = File(io.BytesIO(bytes), name=output)
            if found.exists():
                existing = found.first()
                existing.image.delete()  # remove previous image if new one found
                existing.cloudcover = cloudcover
                existing.image = image
                existing.percent_black = percent_black
                existing.save()
            else:
                SiteImage.objects.create(
                    siteeval=observation.siteeval,
                    siteobs=observation,
                    timestamp=observation.timestamp,
                    image=image,
                    cloudcover=cloudcover,
                    source=baseConstellation,
                    percent_black=percent_black,
                )

    # Now we need to go through and find all other images
    # that exist in the start/end range of the siteEval
    timebuffer = ((max_time + timedelta(days=30)) - (min_time - timedelta(days=30))) / 2
    timestamp = (min_time + timedelta(days=30)) + timebuffer
    # Now we get a list of all the timestamps and captures that fall in this range.
    worldView = baseConstellation == 'WV'
    captures = get_range_captures(
        max_bbox, timestamp, matchConstellation, timebuffer, worldView
    )
    count = 0
    for (
        capture
    ) in (
        captures
    ):  # Now we go through the list and add in a timestmap if it doesn't exist
        if capture.timestamp not in found_timestamps.keys():
            # we need to add a new image into the structure
            bytes = None
            if worldView:
                bytes = get_worldview_processed_visual_bbox(capture, bbox)
            else:
                bytes = get_raster_bbox(capture.uri, bbox)
            if bytes is None:
                logger.warning(f'COULD NOT FIND ANY IMAGE FOR TIMESTAMP: {timestamp}')
                continue
            percent_black = get_percent_black_pixels(bytes)
            cloudcover = capture.cloudcover
            count += 1
            output = f'tile_image_{observation.siteeval}_nonobs_{count}.jpg'
            image = File(io.BytesIO(bytes), name=output)
            found = SiteImage.objects.filter(
                siteeval=baseSiteEval,
                timestamp=capture.timestamp,
                source=baseConstellation,
            )
            if found.exists():
                existing = found.first()
                existing.image.delete()
                existing.cloudcover = cloudcover
                existing.image = image
                existing.save()
            else:
                SiteImage.objects.create(
                    siteeval=baseSiteEval,
                    timestamp=capture.timestamp,
                    image=image,
                    cloudcover=cloudcover,
                    source=baseConstellation,
                )
                if found.exists():
                    existing = found.first()
                    existing.image.delete()
                    existing.cloudcover = cloudcover
                    existing.image = image
                    existing.percent_black = percent_black
                    existing.save()
                else:
                    SiteImage.objects.create(
                        siteeval=baseSiteEval,
                        timestamp=capture.timestamp,
                        image=image,
                        cloudcover=cloudcover,
                        percent_black=percent_black,
                        source=baseConstellation,
                    )
    fetching_task = SatelliteFetching.objects.get(siteeval_id=site_eval_id)
    fetching_task.status = SatelliteFetching.Status.COMPLETE
    fetching_task.save()
