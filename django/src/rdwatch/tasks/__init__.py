import io
import logging
from collections.abc import Iterable
from datetime import datetime, timedelta

from celery import shared_task
from PIL import Image
from pyproj import Transformer

from django.contrib.gis.geos import Polygon
from django.core.files import File
from django.db import transaction
from django.db.models import DateTimeField, ExpressionWrapper, F
from django.utils import timezone

from rdwatch.celery import app
from rdwatch.models import (
    HyperParameters,
    SatelliteFetching,
    SiteEvaluation,
    SiteImage,
    SiteObservation,
)
from rdwatch.models.lookups import Constellation
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

BaseTime = '2013-01-01'  # lowest time to use if time is null for observations


def is_inside_range(
    timestamps: Iterable[datetime], check_timestamp: datetime, days_range
):
    for timestamp in timestamps:
        time_difference = check_timestamp - timestamp
        if abs(time_difference.days) <= days_range:
            logger.warning(
                f'Skipping Timestamp because difference is: {time_difference.days}'
            )
            return True
    return False


@app.task(bind=True)
def get_siteobservations_images(
    self,
    site_eval_id: int,
    baseConstellation='WV',
    force=False,  # forced downloading found_timestamps again
    dayRange=14,
    no_data_limit=50,
    overrideDates: None | list[datetime, datetime] = None,
) -> None:
    constellationObj = Constellation.objects.filter(slug=baseConstellation).first()
    # Ensure we are using ints for the DayRange and no_data_limit
    dayRange = int(dayRange)
    no_data_limit = int(no_data_limit)
    site_observations = SiteObservation.objects.filter(
        siteeval=site_eval_id
    )  # need a full list for min/max times
    site_obs_count = SiteObservation.objects.filter(
        siteeval=site_eval_id, constellation_id=constellationObj.pk
    ).count()

    transformer = Transformer.from_crs('EPSG:3857', 'EPSG:4326')
    found_timestamps = {}
    min_time = datetime.max
    max_time = datetime.min
    max_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]
    matchConstellation = ''
    baseSiteEval = None
    if site_obs_count == 0:
        baseSiteEval = SiteEvaluation.objects.get(pk=site_eval_id)
        mercator: tuple[float, float, float, float] = baseSiteEval.geom.extent
        tempbox = transformer.transform_bounds(
            mercator[0], mercator[1], mercator[2], mercator[3]
        )
        bbox = [tempbox[1], tempbox[0], tempbox[3], tempbox[2]]
        bbox = scale_bbox(bbox, 1.2)
        max_bbox = get_max_bbox(bbox, max_bbox)

    # First we gather all images that match observations
    count = 0
    for observation in site_observations.iterator():
        count += 1
        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': site_obs_count + 1,
                'mode': 'Site Observations',
                'siteEvalId': site_eval_id,
            },
        )
        if observation.timestamp is not None:
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
        logger.warning(timestamp)
        if str(constellation) == baseConstellation and timestamp is not None:
            baseSiteEval = observation.siteeval
            matchConstellation = constellation
            found = SiteImage.objects.filter(
                siteeval=observation.siteeval,
                siteobs=observation,
                timestamp=observation.timestamp,
                source=baseConstellation,
            )
            if (
                baseConstellation in ('S2', 'L8')
                and dayRange > -1
                and is_inside_range(
                    found_timestamps.keys(), observation.timestamp, dayRange
                )
            ):
                logger.warning(f'Skipping Timestamp: {timestamp}')
                count += 1
                continue
            if found.exists() and not force:
                found_timestamps[observation.timestamp] = True
                count += 1
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
            if dayRange != -1 and percent_black < no_data_limit:
                found_timestamps[found_timestamp] = True
            elif dayRange == -1:
                found_timestamps[found_timestamp] = True
            # logger.warning(f'Retrieved Image with timestamp: {timestamp}')
            output = f'tile_image_{observation.id}.jpg'
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
                    siteeval=observation.siteeval,
                    siteobs=observation,
                    timestamp=observation.timestamp,
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
    if overrideDates:
        min_time = datetime.strptime(overrideDates[0], '%Y-%m-%d')
        max_time = datetime.strptime(overrideDates[1], '%Y-%m-%d')
    else:
        if min_time == datetime.max:
            min_time = datetime.strptime(BaseTime, '%Y-%m-%d')
        if max_time == datetime.min:
            max_time = datetime.now()
    timebuffer = ((max_time + timedelta(days=30)) - (min_time - timedelta(days=30))) / 2
    timestamp = (min_time + timedelta(days=30)) + timebuffer

    # Now we get a list of all the timestamps and captures that fall in this range.
    worldView = baseConstellation == 'WV'
    if matchConstellation == '':
        matchConstellation = Constellation.objects.filter(
            slug=baseConstellation
        ).first()
        logger.warning(
            f'Utilizing Constellation: {matchConstellation} - {matchConstellation.slug}'
        )

    print('Min')
    print(min_time)
    print('Max')
    print(max_time)
    print('Buffer')
    print(timebuffer)
    print('Override')
    print(overrideDates)
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
    if (
        baseSiteEval is None
    ):  # We need to grab the siteEvaluation directly for a reference
        baseSiteEval = SiteEvaluation.objects.filter(pk=site_eval_id).first()
    count = 0
    logger.warning(f'Found {len(captures)} captures')
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
                bytes = get_worldview_processed_visual_bbox(capture, max_bbox)
            else:
                bytes = get_raster_bbox(capture.uri, max_bbox)
            if bytes is None:
                logger.warning(f'COULD NOT FIND ANY IMAGE FOR TIMESTAMP: {timestamp}')
                continue
            percent_black = get_percent_black_pixels(bytes)
            cloudcover = capture.cloudcover
            count += 1
            output = f'tile_image_{baseSiteEval.pk}_nonobs_{count}.jpg'
            image = File(io.BytesIO(bytes), name=output)
            imageObj = Image.open(io.BytesIO(bytes))
            if image is None:  # No null/None images should be set
                continue
            found = SiteImage.objects.filter(
                siteeval=baseSiteEval,
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
                    siteeval=baseSiteEval,
                    timestamp=capture_timestamp,
                    aws_location=capture.uri,
                    image=image,
                    cloudcover=cloudcover,
                    percent_black=percent_black,
                    source=baseConstellation,
                    image_bbox=Polygon.from_bbox(max_bbox),
                    image_dimensions=[imageObj.width, imageObj.height],
                )
    fetching_task = SatelliteFetching.objects.get(siteeval_id=site_eval_id)
    fetching_task.status = SatelliteFetching.Status.COMPLETE
    fetching_task.celery_id = ''
    fetching_task.save()


@shared_task
def delete_temp_model_runs_task() -> None:
    """Delete all model runs that are due to be deleted."""
    model_runs_to_delete = (
        HyperParameters.objects.filter(expiration_time__isnull=False)
        .alias(
            delete_at=ExpressionWrapper(
                F('created') + F('expiration_time'), output_field=DateTimeField()
            )
        )
        .filter(delete_at__lte=timezone.now())
    )

    with transaction.atomic():
        SiteObservation.objects.filter(
            siteeval__configuration__in=model_runs_to_delete
        ).delete()
        SiteEvaluation.objects.filter(configuration__in=model_runs_to_delete).delete()
        model_runs_to_delete.delete()
