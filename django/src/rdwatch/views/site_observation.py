from datetime import datetime
from typing import Literal

from celery.result import AsyncResult
from ninja import Router, Schema
from pydantic import UUID4

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.gis.db.models.functions import Area, Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count, Max, Min
from django.db.models.functions import JSONObject  # type: ignore
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import (
    SatelliteFetching,
    SiteEvaluation,
    SiteImage,
    SiteObservation,
    SiteObservationTracking,
    lookups,
)
from rdwatch.schemas import SiteObservationRequest
from rdwatch.schemas.common import BoundingBoxSchema, TimeRangeSchema
from rdwatch.tasks import get_siteobservations_images

router = Router()


class SiteObservationSchema(Schema):
    id: UUID4
    label: str
    score: float
    constellation: str | None
    spectrum: str | None
    timestamp: int | None
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
    timestamp: int | None
    status: str | None
    bbox: BoundingBoxSchema
    results: list[SiteObservationSchema]
    images: SiteEvaluationImageListSchema
    job: JobStatusSchema | None


@router.get('/{evaluation_id}/', response={200: SiteObservationsListSchema})
def site_observations(request: HttpRequest, evaluation_id: UUID4):
    if not SiteEvaluation.objects.filter(pk=evaluation_id).exists():
        raise Http404()
    site_eval_data = SiteEvaluation.objects.filter(pk=evaluation_id).aggregate(
        timerange=JSONObject(
            min=ExtractEpoch(Min('start_date')),
            max=ExtractEpoch(Max('end_date')),
        ),
        bbox=BoundingBox(Collect('geom')),
    )
    queryset = (
        SiteObservation.objects.order_by('timestamp')
        .filter(siteeval__id=evaluation_id)
        .aggregate(
            count=Count('pk'),
            bbox=BoundingBox(Collect('geom')),
            results=JSONBAgg(
                JSONObject(
                    id='pk',
                    label='label__slug',
                    score='score',
                    constellation='constellation__slug',
                    spectrum='spectrum__slug',
                    timestamp=ExtractEpoch('timestamp'),
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

    for image in image_queryset['results']:
        image['image'] = default_storage.url(image['image'])
    queryset['images'] = image_queryset
    queryset['timerange'] = site_eval_data['timerange']
    replace_bbox = False
    for key in queryset['bbox'].keys():
        if queryset['bbox'][key] is None:  # Some Evals have no site Observations,
            # need to replace the bounding box in this case
            replace_bbox = True
    if replace_bbox:
        queryset['bbox'] = site_eval_data['bbox']
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
def get_site_observation_images(
    request: HttpRequest,
    evaluation_id: UUID4,
    constellation: Literal['WV', 'S2', 'L8'] = 'WV',
    dayRange: int = 14,
    noData: int = 50,
    overrideDates: None | list[str] = None,
):
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
                return 409, 'Image generation already in progress.'
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
        task_id = get_siteobservations_images.delay(
            evaluation_id,
            constellation,
            False,
            dayRange,
            noData,
            overrideDates,
        )
        fetching_task.celery_id = task_id.id
        fetching_task.save()
    return 202, True


@router.put(
    '/{evaluation_id}/cancel-generate-images/', response={202: bool, 409: str, 404: str}
)
def cancel_site_observation_images(request: HttpRequest, evaluation_id: UUID4):
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


@router.patch('/{id}/')
def update_site_observation(
    request: HttpRequest, id: UUID4, data: SiteObservationRequest
):
    with transaction.atomic():
        site_observation = get_object_or_404(
            SiteObservation.objects.select_for_update(), pk=id
        )
        # create a copy of it in the history log
        SiteObservationTracking.objects.create(
            timestamp=site_observation.timestamp,
            geom=site_observation.geom,
            score=site_observation.score,
            siteval=site_observation.siteeval,
            notes=site_observation.notes,
            edited=datetime.now(),
            observation=site_observation.pk,
        )

        if data.label:
            site_observation.label = lookups.ObservationLabel.objects.get(
                slug=data.label
            )
        if data.notes:
            site_observation.notes = data.notes
        site_observation.timestamp = data.timestamp
        if data.spectrum:
            site_observation.spectrum = data.spectrum
        if data.constellation:
            site_observation.constellation = lookups.Constellation.objects.get(
                slug=data.label
            )

        site_observation.save()

        return site_observation


@router.put('/{evaluation_id}/')
def add_site_observation(
    request: HttpRequest, evaluation_id: UUID4, data: SiteObservationRequest
):
    site_evaluation = get_object_or_404(SiteEvaluation, pk=evaluation_id)

    if data.label:
        label = lookups.ObservationLabel.objects.get(slug=data.label)

    if data.constellation:
        constellation = lookups.Constellation.objects.get(slug=data.label)

    new_site_observation = SiteObservation.objects.create(
        siteeval=site_evaluation,
        label=label,
        score=data.score,
        geom=data.geom,
        constellation=constellation,
        spectrum=None,
        timestamp=data.timestamp,
    )
    return new_site_observation
