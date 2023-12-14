import io
import json
import logging
import os
import tempfile
import zipfile
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Literal
from uuid import uuid4

from celery import shared_task
from celery.result import AsyncResult
from more_itertools import ichunked
from PIL import Image
from pydantic import UUID4
from pyproj import Transformer

from django.contrib.gis.geos import Polygon
from django.core.files import File
from django.db import transaction
from django.db.models import DateTimeField, ExpressionWrapper, F
from django.utils import timezone

from rdwatch.celery import app
from rdwatch.models import (
    AnnotationExport,
    ModelRun,
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
from rdwatch.views.site_evaluation import get_site_model_feature_JSON

logger = logging.getLogger(__name__)
# lowest time to use if time is null for observations
BaseTime = '2013-01-01'
# Default scale multiplier for bounding box to provide more area
BboxScaleDefault = 1.2
# rough number to convert lat/long to Meters
ToMeters = 111139.0
# number in meters to add to the center of small polygons for S2/L8
overrideImageSize = 1000


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
def get_siteobservation_images_task(
    self,
    site_eval_id: UUID4,
    baseConstellations=['WV'],  # noqa
    force=False,  # forced downloading found_timestamps again
    dayRange=14,
    no_data_limit=50,
    overrideDates: None | list[datetime, datetime] = None,
    scale: Literal['default', 'bits'] | list[int] = 'default',
    bboxScale: float = BboxScaleDefault,
) -> None:
    capture_count = 0
    for constellation in baseConstellations:
        capture_count += get_siteobservations_images(
            self,
            site_eval_id=site_eval_id,
            baseConstellation=constellation,
            force=force,
            dayRange=dayRange,
            no_data_limit=no_data_limit,
            overrideDates=overrideDates,
            scale=scale,
            bboxScale=bboxScale,
        )
    fetching_task = SatelliteFetching.objects.get(site_id=site_eval_id)
    fetching_task.status = SatelliteFetching.Status.COMPLETE
    if capture_count == 0:
        fetching_task.error = 'No Captures found'
    fetching_task.celery_id = ''
    fetching_task.save()


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
    max_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]
    matchConstellation = ''
    # Use the base SiteEvaluation extents as the max size
    baseSiteEval = SiteEvaluation.objects.get(pk=site_eval_id)
    # use the Eval Start/End date if not null
    min_time = baseSiteEval.start_date
    max_time = baseSiteEval.end_date
    if min_time is None:
        min_time = datetime.strptime(BaseTime, '%Y-%m-%d')
    if max_time is None:
        max_time = datetime.now()

    mercator: tuple[float, float, float, float] = baseSiteEval.geom.extent
    tempbox = transformer.transform_bounds(
        mercator[0], mercator[1], mercator[2], mercator[3]
    )
    bbox = [tempbox[1], tempbox[0], tempbox[3], tempbox[2]]
    # if width | height is too small we pad S2/L8 regions for more context
    bbox_width = (tempbox[2] - tempbox[0]) * ToMeters
    bbox_height = (tempbox[3] - tempbox[1]) * ToMeters
    if baseConstellation != 'WV' and (
        bbox_width < overrideImageSize or bbox_height < overrideImageSize
    ):
        size_diff = (
            overrideImageSize * 0.5
        ) / ToMeters  # find how much to add to each lon/lat
        bbox = [
            tempbox[1] - size_diff,
            tempbox[0] - size_diff,
            tempbox[3] + size_diff,
            tempbox[2] + size_diff,
        ]
    # add the included padding to the updated BBOX
    bbox = scale_bbox(bbox, bboxScale)
    # get the updated BBOX if it's bigger
    max_bbox = get_max_bbox(bbox, max_bbox)

    # First we gather all images that match observations
    count = 0
    downloaded_count = 0
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
        if observation.timestamp is not None:
            min_time = min(min_time, observation.timestamp)
            max_time = max(max_time, observation.timestamp)
        mercator: tuple[float, float, float, float] = observation.geom.extent

        timestamp = observation.timestamp
        constellation = observation.constellation
        # We need to grab the image for this timerange and type
        logger.warning(timestamp)
        if str(constellation) == baseConstellation and timestamp is not None:
            count += 1
            baseSiteEval = observation.siteeval
            matchConstellation = constellation
            found = SiteImage.objects.filter(
                site=observation.siteeval,
                observation=observation,
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
                continue
            if found.exists() and not force:
                found_timestamps[observation.timestamp] = True
                continue
            results = fetch_boundbox_image(
                bbox, timestamp, constellation.slug, baseConstellation == 'WV', scale
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
            output = f'tile_image_{observation.id}.png'
            image = File(io.BytesIO(bytes), name=output)
            imageObj = Image.open(io.BytesIO(bytes))
            if image is None:  # No null/None images should be set
                continue
            downloaded_count += 1
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
                    site=observation.siteeval,
                    observation=observation,
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
    if overrideDates and len(overrideDates) == 2:
        min_time = datetime.strptime(overrideDates[0], '%Y-%m-%d')
        max_time = datetime.strptime(overrideDates[1], '%Y-%m-%d')
        timebuffer = (max_time - min_time) / 2
        timestamp = min_time + timebuffer
    else:
        timebuffer = (
            (max_time + timedelta(days=30)) - (min_time - timedelta(days=30))
        ) / 2
        timestamp = (min_time - timedelta(days=30)) + timebuffer

    # Now we get a list of all the timestamps and captures that fall in this range.
    worldView = baseConstellation == 'WV'
    if matchConstellation == '':
        matchConstellation = Constellation.objects.filter(
            slug=baseConstellation
        ).first()
        logger.warning(
            f'Utilizing Constellation: {matchConstellation} - {matchConstellation.slug}'
        )

    captures = get_range_captures(
        max_bbox, timestamp, matchConstellation.slug, timebuffer, worldView
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
    count = 1
    num_of_captures = len(captures)
    logger.warning(f'Found {num_of_captures} captures')
    if num_of_captures == 0:
        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': num_of_captures,
                'mode': 'No Captures',
                'siteEvalId': site_eval_id,
            },
        )

    logger.warning(f'Found {num_of_captures} captures')
    for (
        capture
    ) in (
        captures
    ):  # Now we go through the list and add in a timestmap if it doesn't exist
        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': num_of_captures,
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
                site=baseSiteEval,
                timestamp=capture_timestamp,
                source=baseConstellation,
            )
            if dayRange != -1 and percent_black < no_data_limit:
                found_timestamps[capture_timestamp] = True
            elif dayRange == -1:
                found_timestamps[capture_timestamp] = True
            downloaded_count += 1
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
                    site=baseSiteEval,
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
    return downloaded_count


@shared_task
def delete_temp_model_runs_task() -> None:
    """Delete all model runs that are due to be deleted."""
    model_runs_to_delete = (
        ModelRun.objects.filter(expiration_time__isnull=False)
        .alias(
            delete_at=ExpressionWrapper(
                F('created') + F('expiration_time'), output_field=DateTimeField()
            )
        )
        .filter(delete_at__lte=timezone.now())
    )

    with transaction.atomic():
        # Delete observations first, then evaluations, then finally model runs.
        # Due to the number of site evaluations/observations we likely have to
        # delete, we do the deletion in lazily loaded batches of 1,000 rows to
        # avoid blowing up the celery worker's memory.

        # Delete observations
        for observations in ichunked(
            SiteObservation.objects.filter(
                siteeval__configuration__in=model_runs_to_delete
            )
            .values_list('pk', flat=True)
            .iterator(),
            1_000,
        ):
            SiteObservation.objects.filter(pk__in=observations).delete()

        # Delete evaluations
        for evaluations in ichunked(
            SiteEvaluation.objects.filter(configuration__in=model_runs_to_delete)
            .values_list('pk', flat=True)
            .iterator(),
            1_000,
        ):
            SiteEvaluation.objects.filter(pk__in=evaluations).delete()

        # Delete model runs
        for model_runs in ichunked(
            model_runs_to_delete.values_list('pk', flat=True).iterator(),
            1_000,
        ):
            ModelRun.objects.filter(pk__in=model_runs).delete()


@shared_task
def delete_export_files() -> None:
    """Delete all S3 Export Files that are over an hour old."""
    exports_to_delete = AnnotationExport.objects.filter(
        created__lte=timezone.now() - timedelta(hours=1)
    )
    exports_to_delete.delete()


@app.task(bind=True)
def download_annotations(self, id: UUID4, mode: Literal['all', 'approved', 'rejected']):
    # Needs to go through the siteEvaluations and download one for each file
    if mode == 'all':
        site_evals = SiteEvaluation.objects.filter(configuration_id=id)
    elif mode == 'approved':
        site_evals = SiteEvaluation.objects.filter(
            configuration_id=id, status=SiteEvaluation.Status.APPROVED
        )
    elif mode == 'rejected':
        site_evals = SiteEvaluation.objects.filter(
            configuration_id=id, status=SiteEvaluation.Status.REJECTED
        )
    configuration = ModelRun.objects.get(pk=id)
    task_id = self.request.id
    temp_zip_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')

    with tempfile.TemporaryDirectory() as temp_dir:
        file_list = []
        nine_count = 0  # annotations that have Site Id 9999
        for item in site_evals.iterator():
            data, site_id, basefilename = get_site_model_feature_JSON(item.pk)
            modified_site_id = site_id
            if '9999' in site_id:
                nine_count += 1
                modified_site_id = f'{site_id}-{nine_count}'
            file_name = os.path.join(temp_dir, f'{modified_site_id}.json')

            with open(file_name, 'w') as file:
                json.dump(data, file)
            file_list.append(
                {
                    'filename': file_name,
                    'siteId': modified_site_id,
                    'baseName': basefilename,
                }
            )
        with zipfile.ZipFile(temp_zip_file, 'w') as zipf:
            for item in file_list:
                zipf.write(item['filename'], f"{item['siteId']}.geojson")
        annotation_export = AnnotationExport.objects.create(
            configuration=configuration,
            name=configuration.title,
            celery_id=task_id,
            created=datetime.now(),
        )
        annotation_export.export_file.save(f'{task_id}.zip', File(temp_zip_file))
        temp_zip_file.close()


@shared_task
def cancel_generate_images_task(model_run_id: UUID4) -> None:
    site_evaluations = SiteEvaluation.objects.filter(configuration=model_run_id)

    for eval in site_evaluations.iterator():
        with transaction.atomic():
            # Use select_for_update here to lock the SatelliteFetching row
            # for the duration of this transaction in order to ensure its
            # status doesn't change out from under us
            fetching_task = (
                SatelliteFetching.objects.select_for_update()
                .filter(site=eval.pk)
                .first()
            )
            if fetching_task is not None:
                if fetching_task.status == SatelliteFetching.Status.RUNNING:
                    if fetching_task.celery_id != '':
                        task = AsyncResult(fetching_task.celery_id)
                        task.revoke(terminate=True)
                    fetching_task.status = SatelliteFetching.Status.COMPLETE
                    fetching_task.celery_id = ''
                    fetching_task.save()


@shared_task
def generate_site_images(
    evaluation_id: UUID4,
    constellation=['WV'],  # noqa
    force=False,  # forced downloading found_timestamps again
    dayRange=14,
    noData=50,
    overrideDates: None | list[datetime, datetime] = None,
    scale: Literal['default', 'bits'] | list[int] = 'default',
    bboxScale: float = BboxScaleDefault,
):
    siteeval = SiteEvaluation.objects.get(pk=evaluation_id)
    with transaction.atomic():
        # Use select_for_update here to lock the SatelliteFetching row
        # for the duration of this transaction in order to ensure its
        # status doesn't change out from under us
        fetching_task = (
            SatelliteFetching.objects.select_for_update().filter(site=siteeval).first()
        )
        if fetching_task is not None:
            # If the task already exists and is running, return a 409 and do not
            # start another one.
            if fetching_task.status == SatelliteFetching.Status.RUNNING:
                return 409, 'Image generation already in progress.'
            # Otherwise, if the task exists but is *not* running, set the status
            # to running and kick off the task
            fetching_task.status = SatelliteFetching.Status.RUNNING
            fetching_task.save()
        else:
            fetching_task = SatelliteFetching.objects.create(
                site=siteeval,
                timestamp=datetime.now(),
                status=SatelliteFetching.Status.RUNNING,
            )
        task_id = get_siteobservation_images_task.delay(
            evaluation_id,
            constellation,
            force,
            dayRange,
            noData,
            overrideDates,
            scale,
            bboxScale,
        )
        fetching_task.celery_id = task_id.id
        fetching_task.save()


@shared_task
def generate_site_images_for_evaluation_run(
    model_run_id: UUID4,
    constellation=['WV'],  # noqa
    force=False,  # forced downloading found_timestamps again
    dayRange=14,
    noData=50,
    overrideDates: None | list[datetime, datetime] = None,
    scale: Literal['default', 'bits'] | list[int] = 'default',
    bboxScale: float = BboxScaleDefault,
):
    sites = SiteEvaluation.objects.filter(configuration=model_run_id)
    for eval in sites.iterator():
        generate_site_images.delay(
            eval.pk,
            constellation,
            force,
            dayRange,
            noData,
            overrideDates,
            scale,
            bboxScale,
        )
