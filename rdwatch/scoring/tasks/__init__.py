import io
import logging
from datetime import date, datetime, timedelta
from typing import Literal
from uuid import uuid4

from celery import shared_task
from celery.result import AsyncResult
from PIL import Image
from pydantic import UUID4

from django.contrib.gis.geos import Point, Polygon
from django.core.files import File
from django.db import transaction

from rdwatch.celery import app
from rdwatch.core.tasks import (
    BaseTime,
    BboxScaleDefault,
    ToMeters,
    get_worldview_nitf_bbox,
    get_worldview_processed_visual_bbox,
    is_inside_range,
    overrideImageSize,
    pointAreaDefault,
)
from rdwatch.core.utils.images import (
    fetch_boundbox_image,
    get_max_bbox,
    get_percent_black_pixels,
    get_range_captures,
    scale_bbox,
)
from rdwatch.core.utils.raster_tile import get_raster_bbox
from rdwatch.scoring.models import (
    AnnotationProposalObservation,
    AnnotationProposalSet,
    AnnotationProposalSite,
    EvaluationRun,
    Observation,
    SatelliteFetching,
    Site,
    SiteImage,
)

logger = logging.getLogger(__name__)


@app.task(bind=True)
def get_siteobservation_images_task(
    self,
    site_eval_id: UUID4,
    baseConstellations=['WV'],  # noqa
    force=False,  # forced downloading found_timestamps again
    dayRange=14,
    no_data_limit=50,
    overrideDates: None | list[datetime, datetime] = None,
    scale: Literal['default', 'bits'] | list[int] = 'bits',
    bboxScale: float = BboxScaleDefault,
    pointArea: float = pointAreaDefault,
    worldview_source: Literal['cog', 'nitf'] | None = 'cog',
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
            pointArea=pointArea,
            worldview_source=worldview_source,
        )
    fetching_task = SatelliteFetching.objects.get(site=site_eval_id)
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
    scale: Literal['default', 'bits'] | list[int] = 'bits',
    bboxScale: float = BboxScaleDefault,
    pointArea: float = pointAreaDefault,
    worldview_source: Literal['cog', 'nitf'] | None = 'cog',
) -> None:
    # Ensure we are using ints for the DayRange and no_data_limit
    dayRange = int(dayRange)
    no_data_limit = int(no_data_limit)
    found_timestamps = {}
    max_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]

    # Use the base SiteEvaluation extents as the max size
    try:
        base_site_eval = Site.objects.get(pk=site_eval_id)
        site_db_model = Site
        geometry = base_site_eval.union_geometry
        # check if geometry is null and use point
        if not geometry:
            point = Point.from_ewkt(base_site_eval.point_geometry)
            geometry = Polygon(
                (
                    (point.x, point.y),
                    (point.x, point.y),
                    (point.x, point.y),
                    (point.x, point.y),
                    (point.x, point.y),
                )
            ).ewkt
        site_observations = Observation.objects.filter(
            site_uuid=site_eval_id
        )  # need a full list for min/max times
        site_obs_count = Observation.objects.filter(
            site_uuid=site_eval_id, sensor=baseConstellation
        ).count()
        proposal = False
    except Site.DoesNotExist:
        base_site_eval = AnnotationProposalSite.objects.get(pk=site_eval_id)
        site_db_model = AnnotationProposalSite
        geometry = base_site_eval.geometry
        site_observations = AnnotationProposalObservation.objects.filter(
            annotation_proposal_site_uuid=site_eval_id
        )  # need a full list for min/max times
        site_obs_count = AnnotationProposalObservation.objects.filter(
            annotation_proposal_site_uuid=site_eval_id, sensor_name=baseConstellation
        ).count()
        proposal = True

    # use the Eval Start/End date if not null
    min_time = base_site_eval.start_date
    max_time = base_site_eval.end_date

    if min_time is None:
        min_time = datetime.strptime(BaseTime, '%Y-%m-%d')
    else:
        min_time = datetime.combine(min_time, datetime.min.time())

    if max_time is None:
        max_time = datetime.now()
    else:
        max_time = datetime.combine(max_time, datetime.min.time())

    tempbox: tuple[float, float, float, float] = Polygon.from_ewkt(geometry).extent
    # check if data is a point instead of geometry
    if (
        tempbox[2] == tempbox[0] and tempbox[3] == tempbox[1]
    ):  # create bbox based on pointArea
        size_diff = (pointArea * 0.5) / ToMeters
        tempbox = [
            tempbox[0] - size_diff,
            tempbox[1] - size_diff,
            tempbox[2] + size_diff,
            tempbox[3] + size_diff,
        ]

    bbox = [tempbox[1], tempbox[0], tempbox[3], tempbox[2]]
    # if width | height is too small we pad S2/L8/PL regions for more context
    bbox_width = (bbox[2] - bbox[0]) * ToMeters
    bbox_height = (bbox[3] - bbox[1]) * ToMeters
    logger.warning('BBOX')
    logger.warning(bbox)
    logger.warning(bbox_width)
    logger.warning(bbox_height)
    if baseConstellation != 'WV' and (
        bbox_width < overrideImageSize or bbox_height < overrideImageSize
    ):
        size_diff = (
            overrideImageSize * 0.5
        ) / ToMeters  # find how much to add to each lon/lat
        bbox = [
            bbox[0] - size_diff,
            bbox[1] - size_diff,
            bbox[2] + size_diff,
            bbox[3] + size_diff,
        ]
    # add the included padding to the updated BBOX
    bbox = scale_bbox(bbox, bboxScale)
    # get the updated BBOX if it's bigger
    max_bbox = get_max_bbox(bbox, max_bbox)
    logger.warning(max_bbox)

    # First we gather all images that match observations
    count = 0
    downloaded_count = 0
    for observation in site_observations.iterator():
        break
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
            obs__time = datetime.combine(observation.date, datetime.min.time())
            min_time = min(min_time, obs__time)
            max_time = max(max_time, obs__time)
        mercator: tuple[float, float, float, float] = Polygon.from_ewkt(
            observation.geometry
        ).extent

        print(mercator)

        timestamp = observation.date

        if isinstance(timestamp, date):
            timestamp = datetime.combine(timestamp, datetime.min.time())

        constellation = (
            observation.sensor_name if proposal else observation.sensor_name or 'WV'
        )
        # We need to grab the image for this timerange and type
        logger.warning(timestamp)
        if str(constellation) == baseConstellation and timestamp is not None:
            count += 1
            base_site_eval = site_eval_id
            found = SiteImage.objects.filter(
                site=site_eval_id,
                observation=observation,
                timestamp=observation.date,
                source=baseConstellation,
            )
            if (
                baseConstellation in ('S2', 'L8', 'PL')
                and dayRange > -1
                and is_inside_range(found_timestamps.keys(), observation.date, dayRange)
            ):
                logger.warning(f'Skipping Timestamp: {timestamp}')
                continue
            if found.exists() and not force:
                found_timestamps[observation.date] = True
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
            output = f'tile_image_{observation.pk}.png'
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
                    site=site_eval_id,
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
        timebuffer = (max_time - min_time) / 2
        timestamp = min_time + timebuffer
    else:
        timebuffer = (
            (max_time + timedelta(days=30)) - (min_time - timedelta(days=30))
        ) / 2
        timestamp = (min_time - timedelta(days=30)) + timebuffer

    # Now we get a list of all the timestamps and captures that fall in this range.
    logger.warning('MAXBBOX')
    logger.warning(max_bbox)
    logger.warning('timestamp')
    logger.warning(timestamp)
    logger.warning(timebuffer)
    captures = get_range_captures(
        max_bbox, timestamp, baseConstellation, timebuffer, worldview_source
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
        base_site_eval is None
    ):  # We need to grab the siteEvaluation directly for a reference
        base_site_eval = site_db_model.objects.filter(pk=site_eval_id).first()
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
                'source': baseConstellation,
                'siteEvalId': site_eval_id,
            },
        )

    # Now we go through the list and add in a timestmap if it doesn't exist
    for capture in captures:
        self.update_state(
            state='PROGRESS',
            meta={
                'current': count,
                'total': num_of_captures,
                'mode': 'Image Captures',
                'source': baseConstellation,
                'siteEvalId': site_eval_id,
            },
        )
        capture_timestamp = capture.timestamp.replace(microsecond=0)
        if (
            baseConstellation in ('S2', 'L8', 'PL')
            and dayRange > -1
            and is_inside_range(found_timestamps.keys(), capture_timestamp, dayRange)
        ):
            count += 1
            continue

        if capture_timestamp not in found_timestamps.keys():
            # we need to add a new image into the structure
            bytes = None
            if baseConstellation == 'WV' and worldview_source == 'cog':
                bytes = get_worldview_processed_visual_bbox(
                    capture, max_bbox, 'PNG', scale
                )
            elif baseConstellation == 'WV' and worldview_source == 'nitf':
                bytes = get_worldview_nitf_bbox(capture, max_bbox, 'PNG', scale)
            else:
                bytes = get_raster_bbox(capture.uri, max_bbox, 'PNG', scale)
            if bytes is None:
                count += 1
                logger.warning(f'COULD NOT FIND ANY IMAGE FOR TIMESTAMP: {timestamp}')
                continue
            percent_black = get_percent_black_pixels(bytes)
            cloudcover = capture.cloudcover
            count += 1
            output = f'tile_image_{base_site_eval.pk}_nonobs_{uuid4()}.png'
            image = File(io.BytesIO(bytes), name=output)
            imageObj = Image.open(io.BytesIO(bytes))
            if image is None:  # No null/None images should be set
                count += 1
                continue
            found = SiteImage.objects.filter(
                site=base_site_eval.pk,
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
                    site=base_site_eval.pk,
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
def cancel_generate_images_task(model_run_uuid: UUID4) -> None:
    try:
        EvaluationRun.objects.get(pk=model_run_uuid)
        sites = Site.objects.filter(evaluation_run_uuid=model_run_uuid)
    except EvaluationRun.DoesNotExist:
        AnnotationProposalSet.objects.get(pk=model_run_uuid)
        sites = AnnotationProposalSite.objects.filter(
            annotation_proposal_set_uuid=model_run_uuid
        )

    for site in sites.iterator():
        with transaction.atomic():
            # Use select_for_update here to lock the SatelliteFetching row
            # for the duration of this transaction in order to ensure its
            # status doesn't change out from under us
            fetching_task = (
                SatelliteFetching.objects.select_for_update()
                .filter(site=site.pk)
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
    model_run_uuid: UUID4,
    site_uuid: UUID4,
    constellation=['WV'],  # noqa
    force=False,  # forced downloading found_timestamps again
    dayRange=14,
    noData=50,
    overrideDates: None | list[datetime, datetime] = None,
    scale: Literal['default', 'bits'] | list[int] = 'bits',
    bboxScale: float = BboxScaleDefault,
    pointArea: float = pointAreaDefault,
    worldview_source: Literal['cog', 'nitf'] | None = 'cog',
):
    with transaction.atomic():
        # Use select_for_update here to lock the SatelliteFetching row
        # for the duration of this transaction in order to ensure its
        # status doesn't change out from under us
        fetching_task = (
            SatelliteFetching.objects.select_for_update().filter(site=site_uuid).first()
        )
        if fetching_task is not None:
            # If the task already exists and is running, return a 409 and do not
            # start another one.
            if fetching_task.status == SatelliteFetching.Status.RUNNING:
                return 409, 'Image generation already in progress.'
            # Otherwise, if the task exists but is *not* running, set the status
            # to running and kick off the task
            fetching_task.status = SatelliteFetching.Status.RUNNING
            fetching_task.model_run_uuid = model_run_uuid
            fetching_task.error = ''
            fetching_task.save()
        else:
            fetching_task = SatelliteFetching.objects.create(
                site=site_uuid,
                model_run_uuid=model_run_uuid,
                timestamp=datetime.now(),
                status=SatelliteFetching.Status.RUNNING,
            )
        task_id = get_siteobservation_images_task.delay(
            site_uuid,
            constellation,
            force,
            dayRange,
            noData,
            overrideDates,
            scale,
            bboxScale,
            pointArea,
            worldview_source,
        )
        fetching_task.celery_id = task_id.id
        fetching_task.save()


@shared_task
def generate_site_images_for_evaluation_run(
    model_run_uuid: UUID4,
    constellation=['WV'],  # noqa
    force=False,  # forced downloading found_timestamps again
    dayRange=14,
    noData=50,
    overrideDates: None | list[datetime, datetime] = None,
    scale: Literal['default', 'bits'] | list[int] = 'bits',
    bboxScale: float = BboxScaleDefault,
    pointArea: float = pointAreaDefault,
    worldview_source: Literal['cog', 'nitf'] | None = 'cog',
):
    try:
        EvaluationRun.objects.get(pk=model_run_uuid)
        sites = Site.objects.filter(evaluation_run_uuid=model_run_uuid)
    except EvaluationRun.DoesNotExist:
        AnnotationProposalSet.objects.get(pk=model_run_uuid)
        sites = AnnotationProposalSite.objects.filter(
            annotation_proposal_set_uuid=model_run_uuid
        )

    for site in sites.iterator():
        generate_site_images.delay(
            model_run_uuid,
            site.pk,
            constellation,
            force,
            dayRange,
            noData,
            overrideDates,
            scale,
            bboxScale,
            pointArea,
            worldview_source,
        )
