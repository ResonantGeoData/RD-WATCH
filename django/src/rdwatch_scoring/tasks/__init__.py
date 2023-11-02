import io
import logging
from datetime import date, datetime, timedelta
from typing import Literal
from uuid import uuid4

from PIL import Image
from pydantic import UUID4

from django.contrib.gis.geos import Polygon
from django.core.files import File

from rdwatch.celery import app
from rdwatch.tasks import (
    BaseTime,
    BboxScaleDefault,
    ToMeters,
    get_worldview_processed_visual_bbox,
    is_inside_range,
    overrideImageSize,
)
from rdwatch.utils.images import (
    fetch_boundbox_image,
    get_max_bbox,
    get_percent_black_pixels,
    get_range_captures,
    scale_bbox,
)
from rdwatch.utils.raster_tile import get_raster_bbox
from rdwatch_scoring.models import Observation, SatelliteFetching, Site, SiteImage

logger = logging.getLogger(__name__)


@app.task(bind=True)
def get_siteobservations_images(
    self,
    site_eval_id: UUID4,
    baseConstellation='WV',
    force=False,  # forced downloading found_timestamps again
    dayRange=14,
    no_data_limit=50,
    overrideDates: None | list[datetime, datetime] = None,
    scale: Literal['default', 'bits'] | list[int] = 'default',
    bboxScale: float = BboxScaleDefault,
) -> None:
    # Ensure we are using ints for the DayRange and no_data_limit
    dayRange = int(dayRange)
    no_data_limit = int(no_data_limit)
    site_observations = Observation.objects.filter(
        site_uuid=site_eval_id
    )  # need a full list for min/max times
    site_obs_count = Observation.objects.filter(
        site_uuid=site_eval_id, sensor=baseConstellation
    ).count()
    found_timestamps = {}
    max_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]
    # Use the base SiteEvaluation extents as the max size
    baseSiteEval = Site.objects.get(pk=site_eval_id)

    # use the Eval Start/End date if not null
    min_time = baseSiteEval.start_date
    max_time = baseSiteEval.end_date

    if min_time is None:
        min_time = datetime.strptime(BaseTime, '%Y-%m-%d')
    else:
        min_time = datetime.combine(min_time, datetime.min.time())

    if max_time is None:
        max_time = datetime.now()
    else:
        max_time = datetime.combine(max_time, datetime.min.time())

    bbox: tuple[float, float, float, float] = Polygon.from_ewkt(
        baseSiteEval.union_geometry
    ).extent

    # if width | height is too small we pad S2/L8 regions for more context
    bbox_width = (bbox[2] - bbox[0]) * ToMeters
    bbox_height = (bbox[3] - bbox[1]) * ToMeters
    if baseConstellation != 'WV' and (
        bbox_width < overrideImageSize or bbox_height < overrideImageSize
    ):
        size_diff = (
            overrideImageSize * 0.5
        ) / ToMeters  # find how much to add to each lon/lat
        bbox = [
            bbox[1] - size_diff,
            bbox[0] - size_diff,
            bbox[3] + size_diff,
            bbox[2] + size_diff,
        ]
    # add the included padding to the updated BBOX
    bbox = scale_bbox(bbox, bboxScale)
    # get the updated BBOX if it's bigger
    max_bbox = get_max_bbox(bbox, max_bbox)

    # First we gather all images that match observations
    count = 0
    for observation in site_observations.iterator():
        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': site_obs_count,
                'mode': 'Site Observations',
                'siteEvalId': site_eval_id,
            },
        )
        if observation.date is not None:
            min_time = min(min_time, observation.date)
            max_time = max(max_time, observation.date)
        mercator: tuple[float, float, float, float] = Polygon.from_ewkt(
            observation.geometry
        ).extent

        print(mercator)

        timestamp = observation.date

        if isinstance(timestamp, date):
            timestamp = datetime.combine(timestamp, datetime.min.time())

        constellation = observation.sensor or 'WV'
        # We need to grab the image for this timerange and type
        logger.warning(timestamp)
        if str(constellation) == baseConstellation and timestamp is not None:
            count += 1
            baseSiteEval = observation.site_uuid
            found = SiteImage.objects.filter(
                site=observation.site_uuid,
                observation=observation,
                timestamp=observation.date,
                source=baseConstellation,
            )
            if (
                baseConstellation in ('S2', 'L8')
                and dayRange > -1
                and is_inside_range(found_timestamps.keys(), observation.date, dayRange)
            ):
                logger.warning(f'Skipping Timestamp: {timestamp}')
                continue
            if found.exists() and not force:
                found_timestamps[observation.date] = True
                continue
            results = fetch_boundbox_image(
                bbox, timestamp, constellation, baseConstellation == 'WV', scale
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
            if dayRange != -1 and percent_black < no_data_limit:
                found_timestamps[found_timestamp] = True
            elif dayRange == -1:
                found_timestamps[found_timestamp] = True
            # logger.warning(f'Retrieved Image with timestamp: {timestamp}')
            output = f'tile_image_{observation.pk}.png'
            image = File(io.BytesIO(bytes), name=output)
            imageObj = Image.open(io.BytesIO(bytes))
            if image is None:  # No null/None images should be set
                continue
            if found.exists():
                existing = found.first()
                existing.image.delete()  # remove previous image if new one found
                existing.cloudcover = cloudcover
                existing.image = image
                existing.percent_black = percent_black
                existing.aws_location = results['uri']
                existing.image_bbox = Polygon.from_bbox(max_bbox)
                existing.image_dimensions = [imageObj.width, imageObj.height]
                existing.save()
            else:
                SiteImage.objects.create(
                    site=observation.site_uuid,
                    observation=observation,
                    timestamp=observation.date,
                    image=image,
                    aws_location=results['uri'],
                    cloudcover=cloudcover,
                    source=baseConstellation,
                    percent_black=percent_black,
                    image_bbox=Polygon.from_bbox(max_bbox),
                    image_dimensions=[imageObj.width, imageObj.height],
                )

    # Now we need to go through and find all other images
    # that exist in the start/end range of the siteEval
    if overrideDates and len(overrideDates) == 2:
        min_time = datetime.strptime(overrideDates[0], '%Y-%m-%d')
        max_time = datetime.strptime(overrideDates[1], '%Y-%m-%d')

    timebuffer = ((max_time + timedelta(days=30)) - (min_time - timedelta(days=30))) / 2
    # print(timebuffer)
    timestamp = (min_time + timedelta(days=30)) + timebuffer

    # Now we get a list of all the timestamps and captures that fall in this range.
    worldView = baseConstellation == 'WV'

    captures = get_range_captures(
        max_bbox, timestamp, baseConstellation, timebuffer, worldView
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
    if (
        baseSiteEval is None
    ):  # We need to grab the siteEvaluation directly for a reference
        baseSiteEval = Site.objects.filter(pk=site_eval_id).first()
    count = 1
    logger.warning(f'Found {len(captures)} captures')
    # Now we go through the list and add in a timestmap if it doesn't exist
    for capture in captures:
        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': len(captures),
                'mode': 'Image Captures',
                'siteEvalId': site_eval_id,
            },
        )
        capture_timestamp = capture.timestamp.replace(microsecond=0)
        if (
            (baseConstellation == 'S2' or baseConstellation == 'L8')
            and dayRange > -1
            and is_inside_range(found_timestamps.keys(), capture_timestamp, dayRange)
        ):
            count += 1
            continue

        if capture_timestamp not in found_timestamps.keys():
            # we need to add a new image into the structure
            bytes = None
            if worldView:
                bytes = get_worldview_processed_visual_bbox(
                    capture, max_bbox, 'PNG', scale
                )
            else:
                bytes = get_raster_bbox(capture.uri, max_bbox, 'PNG', scale)
            if bytes is None:
                count += 1
                logger.warning(f'COULD NOT FIND ANY IMAGE FOR TIMESTAMP: {timestamp}')
                continue
            percent_black = get_percent_black_pixels(bytes)
            cloudcover = capture.cloudcover
            count += 1
            output = f'tile_image_{baseSiteEval.pk}_nonobs_{uuid4()}.png'
            image = File(io.BytesIO(bytes), name=output)
            imageObj = Image.open(io.BytesIO(bytes))
            if image is None:  # No null/None images should be set
                count += 1
                continue
            found = SiteImage.objects.filter(
                site=baseSiteEval.pk,
                timestamp=capture_timestamp,
                source=baseConstellation,
            )
            if dayRange != -1 and percent_black < no_data_limit:
                found_timestamps[capture_timestamp] = True
            elif dayRange == -1:
                found_timestamps[capture_timestamp] = True
            if found.exists():
                existing = found.first()
                existing.image.delete()
                existing.cloudcover = cloudcover
                existing.image = image
                existing.aws_location = capture.uri
                existing.image_bbox = Polygon.from_bbox(max_bbox)
                existing.image_dimensions = [imageObj.width, imageObj.height]
                existing.save()
            else:
                SiteImage.objects.create(
                    site=baseSiteEval.pk,
                    timestamp=capture_timestamp,
                    aws_location=capture.uri,
                    image=image,
                    cloudcover=cloudcover,
                    percent_black=percent_black,
                    source=baseConstellation,
                    image_bbox=Polygon.from_bbox(max_bbox),
                    image_dimensions=[imageObj.width, imageObj.height],
                )
        else:
            count += 1
    fetching_task = SatelliteFetching.objects.get(site=site_eval_id)
    fetching_task.status = SatelliteFetching.Status.COMPLETE
    fetching_task.celery_id = ''
    fetching_task.save()
