from datetime import datetime

from celery.result import AsyncResult
from ninja import Router, Schema

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.gis.db.models.functions import Area, Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.db import transaction
from django.db.models import Count, F, Max, Min, RowRange, Window
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SatelliteFetching, SiteEvaluation, SiteImage, SiteObservation
from rdwatch.schemas.common import BoundingBoxSchema, TimeRangeSchema
from rdwatch.tasks import get_siteobservations_images

router = Router()


class SiteObservationSchema(Schema):
    id: int
    label: str
    score: float
    constellation: str
    spectrum: str | None
    timestamp: int | None
    timerange: TimeRangeSchema | None
    bbox: BoundingBoxSchema
    area: float


class SiteEvaluationImageSchema(Schema):
    id: int
    timestamp: int
    image: str
    cloudcover: float
    percent_black: float
    source: str
    siteobs_id: int | None
    bbox: BoundingBoxSchema
    image_dimensions: list[int]
    aws_location: str


class SiteEvaluationImageListSchema(Schema):
    count: int
    results: list[SiteEvaluationImageSchema]


class SiteEvaluationListSchema(Schema):
    count: int
    results: list[SiteEvaluationImageSchema]


class JobStatusSchema(Schema):
    status: str
    error: str | None = None
    timestamp: int
    celery: dict  # celery information for task


class SiteObservationsListSchema(Schema):
    count: int
    timerange: TimeRangeSchema | None
    bbox: BoundingBoxSchema
    results: list[SiteObservationSchema]
    images: SiteEvaluationImageListSchema
    job: JobStatusSchema | None


@router.get('/{evaluation_id}/', response={200: SiteObservationsListSchema})
def site_observations(request: HttpRequest, evaluation_id: int):
    if not SiteEvaluation.objects.filter(pk=evaluation_id).exists():
        raise NotFound()
    queryset = (
        SiteObservation.objects.order_by('timestamp')
        .filter(siteeval__id=evaluation_id)
        .annotate(
            timemin=F('timestamp'),
            timemax=Window(
                expression=Max('timestamp'),
                partition_by=[F('siteeval')],
                frame=RowRange(start=0, end=1),
                order_by='timestamp',  # type: ignore
            ),
        )
        .aggregate(
            count=Count('pk'),
            timerange=JSONObject(
                min=ExtractEpoch(Min('timestamp')),
                max=ExtractEpoch(Max('timestamp')),
            ),
            bbox=BoundingBox(Collect('geom')),
            results=JSONBAgg(
                JSONObject(
                    id='pk',
                    label='label__slug',
                    score='score',
                    constellation='constellation__slug',
                    spectrum='spectrum__slug',
                    timestamp=ExtractEpoch('timestamp'),
                    timerange=JSONObject(
                        min=ExtractEpoch('timemin'),
                        max=ExtractEpoch('timemax'),
                    ),
                    bbox=BoundingBox('geom'),
                    area=Area(Transform('geom', srid=6933)),
                )
            ),
        )
    )
    image_queryset = (
        SiteImage.objects.filter(siteeval__id=evaluation_id)
        .order_by('timestamp')
        .aggregate(
            count=Count('pk'),
            results=JSONBAgg(
                JSONObject(
                    id='pk',
                    timestamp=ExtractEpoch('timestamp'),
                    image='image',
                    cloudcover='cloudcover',
                    percent_black='percent_black',
                    source='source',
                    siteobs_id='siteobs_id',
                    bbox=BoundingBox('image_bbox'),
                    image_dimensions='image_dimensions',
                    aws_location='aws_location',
                )
            ),
        )
    )

    image_queryset
    queryset['images'] = image_queryset
    if SatelliteFetching.objects.filter(siteeval=evaluation_id).exists():
        retrieved = SatelliteFetching.objects.filter(siteeval=evaluation_id).first()
        celery_data = {}
        if retrieved.celery_id:
            task = AsyncResult(retrieved.celery_id)
            celery_data['state'] = task.state
            celery_data['status'] = task.status
            celery_data['info'] = (
                str(task.info) if isinstance(task.info, RuntimeError) else task.info
            )

        queryset['job'] = {
            'status': retrieved.status,
            'error': retrieved.error,
            'timestamp': retrieved.timestamp.timestamp(),
            'celery': celery_data,
        }
    return queryset


@router.post('/{evaluation_id}/generate-images/', response={202: bool, 409: str})
def get_site_observation_images(request: HttpRequest, evaluation_id: int):
    if 'constellation' not in request.GET:
        constellation = 'WV'
    else:
        constellation = request.GET['constellation']

    # Make sure site evaluation actually exists
    siteeval = get_object_or_404(SiteEvaluation, pk=evaluation_id)

    with transaction.atomic():
        # Use select_for_update here to lock the SatelliteFetching row
        # for the duration of this transaction in order to ensure its
        # status doesn't change out from under us
        fetching_task = (
            SatelliteFetching.objects.select_for_update()
            .filter(siteeval=siteeval)
            .first()
        )
        if fetching_task is not None:
            # If the task already exists and is running, return a 409 and do not
            # start another one.
            if fetching_task.status == SatelliteFetching.Status.RUNNING:
                return status.HTTP_409_CONFLICT, 'Image generation already in progress.'
            # Otherwise, if the task exists but is *not* running, set the status
            # to running and kick off the task
            fetching_task.status = SatelliteFetching.Status.RUNNING
            fetching_task.save()
        else:
            fetching_task = SatelliteFetching.objects.create(
                siteeval=siteeval,
                timestamp=datetime.now(),
                status=SatelliteFetching.Status.RUNNING,
            )
        task_id = get_siteobservations_images.delay(evaluation_id, constellation)
        fetching_task.celery_id = task_id.id
        fetching_task.save()
    return 202, True


@router.put(
    '/{evaluation_id}/cancel-generate-images/', response={202: bool, 409: str, 404: str}
)
def cancel_site_observation_images(request: HttpRequest, evaluation_id: int):
    siteeval = get_object_or_404(SiteEvaluation, pk=evaluation_id)

    with transaction.atomic():
        # Use select_for_update here to lock the SatelliteFetching row
        # for the duration of this transaction in order to ensure its
        # status doesn't change out from under us
        fetching_task = (
            SatelliteFetching.objects.select_for_update()
            .filter(siteeval=siteeval)
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
            else:
                return (
                    409,
                    f'There is no running task for Observation Id: {evaluation_id}',
                )

        else:
            return (
                404,
                f'There is no running task for Observation Id: {evaluation_id}',
            )

    return 202, True
