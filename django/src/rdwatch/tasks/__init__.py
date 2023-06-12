import io
import logging
from datetime import datetime, timedelta

from pyproj import Transformer

from django.core.files import File

from rdwatch.celery import app
from rdwatch.models import SatelliteFetching, SiteImage, SiteObservation
from rdwatch.utils.images import (
    fetch_boundbox_image,
    get_max_bbox,
    get_percent_black_pixels,
    get_range_captures,
    scale_bbox,
)
from rdwatch.utils.raster_tile import get_raster_bbox
from rdwatch.utils.worldview_processed.raster_tile import (
    get_worldview_processed_visual_bbox,
)

logger = logging.getLogger(__name__)


@app.task(bind=True)
def get_siteobservations_images(
    self, site_eval_id: int, baseConstellation='WV', force=False
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
    count = 0
    for observation in site_observations.iterator():
        count += 1
        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': site_observations.count() + 1,
                'mode': 'Site Observations',
                'siteEvalId': site_eval_id,
            },
        )

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
            if image is None:  # No null/None images should be set
                continue
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
    self.update_state(
        state='PROGRESS',
        meta={
            'current': 0,
            'total': 0,
            'mode': 'Searching All Images',
            'siteEvalId': site_eval_id,
        },
    )
    count = 0
    for (
        capture
    ) in (
        captures
    ):  # Now we go through the list and add in a timestmap if it doesn't exist
        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': len(captures) + 1,
                'mode': 'Image Captures',
                'siteEvalId': site_eval_id,
            },
        )

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
            if image is None:  # No null/None images should be set
                continue
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
    fetching_task.celery_id = ''
    fetching_task.save()
