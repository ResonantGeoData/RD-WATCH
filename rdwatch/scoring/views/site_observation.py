import logging
from typing import Any, Literal

from celery.result import AsyncResult
from ninja import Query, Router, Schema
from pydantic import UUID4, root_validator

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.db.models.functions import Area, Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Case, CharField, Count, F, Func, Max, Min, Value, When
from django.db.models.functions import Coalesce, JSONObject
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.core.db.functions import BoundingBox, ExtractEpoch
from rdwatch.core.views.site_observation import SiteObservationsListSchema
from rdwatch.scoring.models import (
    AnnotationProposalObservation,
    AnnotationProposalSite,
    Observation,
    SatelliteFetching,
    Site,
    SiteImage,
)
from rdwatch.scoring.tasks import generate_site_images

logger = logging.getLogger(__name__)

router = Router()


class GenerateImagesSchema(Schema):
    constellation: list[Literal['WV', 'S2', 'L8', 'PL']] = ['WV']
    worldviewSource: Literal['cog', 'nitf'] | None = None
    dayRange: int = 14
    noData: int = 50
    overrideDates: None | list[str] = None
    force: bool = False
    scale: Literal['default', 'bits', 'custom'] = 'bits'
    scaleNum: None | list[int] = None
    bboxScale: None | float = 1.2
    pointArea: None | float = 200

    @root_validator
    def validate_worldview_source(cls, values: dict[str, Any]):
        if 'WV' in values['constellation'] and values['worldviewSource'] is None:
            raise ValueError('worldviewSource is required for WV constellation')
        return values


@router.get('/{evaluation_id}/', response={200: SiteObservationsListSchema})
def site_observations(request: HttpRequest, evaluation_id: UUID4):
    try:
        Site.objects.get(pk=evaluation_id)
        site_db_model = Site
        site_db_model_cols = {'region__geometry': 'region__geometry'}
        observations = Observation.objects.order_by('date').filter(
            site_uuid=evaluation_id
        )
        observation_db_model_cols = {
            'date': 'date',
            'phase': 'phase',
            'sensor': 'sensor',
        }
        proposal = False
    except Site.DoesNotExist:
        get_object_or_404(AnnotationProposalSite, pk=evaluation_id)
        site_db_model = AnnotationProposalSite
        site_db_model_cols = {'region__geometry': 'region_id__geometry'}
        observations = AnnotationProposalObservation.objects.order_by(
            'observation_date'
        ).filter(annotation_proposal_site_uuid=evaluation_id)
        observation_db_model_cols = {
            'date': 'observation_date',
            'phase': 'current_phase',
            'sensor': 'sensor_name',
        }
        proposal = True

    site_eval_data = site_db_model.objects.filter(pk=evaluation_id).aggregate(
        timerange=JSONObject(
            min=Coalesce(
                ExtractEpoch(Min('start_date')), ExtractEpoch(Min('point_date'))
            ),
            max=Coalesce(
                ExtractEpoch(Max('start_date')), ExtractEpoch(Max('point_date'))
            ),
        ),
        bbox=BoundingBox(
            Collect(
                Func(
                    F(site_db_model_cols['region__geometry']),
                    4326,
                    function='ST_GeomFromText',
                    output_field=GeometryField(),
                )
            )
        ),
    )
    queryset = observations.aggregate(
        count=Count('pk'),
        bbox=BoundingBox(
            Collect(
                Func(
                    F('geometry'),
                    4326,
                    function='ST_GeomFromText',
                    output_field=GeometryField(),
                )
            )
        ),
        results=JSONBAgg(
            JSONObject(
                id='pk',
                label=(
                    Func(
                        F(observation_db_model_cols['phase']),
                        Value(', '),
                        function='array_to_string',
                        output=CharField(),
                    )
                    if proposal
                    else observation_db_model_cols['phase']
                ),
                score='score',
                # Default to worldview if sensor is NULL.
                # TODO: what is the expected behavior here?
                constellation=Coalesce(
                    observation_db_model_cols['sensor'], Value(None)
                ),
                # spectrum="spectrum__slug",
                timestamp=ExtractEpoch(observation_db_model_cols['date']),
                bbox=BoundingBox(
                    Func(
                        F('geometry'),
                        4326,
                        function='ST_GeomFromText',
                        output_field=GeometryField(),
                    )
                ),
                area=Area(
                    Transform(
                        Func(
                            F('geometry'),
                            4326,
                            function='ST_GeomFromText',
                            output_field=GeometryField(),
                        ),
                        srid=6933,
                    )
                ),
            ),
            default=[],
        ),
    )
    image_queryset = (
        SiteImage.objects.filter(site=evaluation_id)
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
                    observation_id=Case(
                        When(observation__exact='', then=None),
                        When(observation__isnull=False, then='observation'),
                        default=Value(None),
                    ),
                    bbox=BoundingBox('image_bbox'),
                    image_dimensions='image_dimensions',
                    uri_locations='uri_locations',
                ),
                default=[],
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
    if SatelliteFetching.objects.filter(site=evaluation_id).exists():
        retrieved = SatelliteFetching.objects.filter(site=evaluation_id).first()
        celery_data = {}
        if retrieved.celery_id:
            task = AsyncResult(retrieved.celery_id)
            celery_data['state'] = task.state
            celery_data['status'] = task.status
            celery_data['info'] = (
                str(task.info) if isinstance(task.info, Exception) else task.info
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
    params: GenerateImagesSchema = Query(...),  # noqa: B008
):
    try:
        model_run_uuid = (
            Site.objects.filter(uuid=evaluation_id)
            .values_list('evaluation_run_uuid', flat=True)
            .first()
        )
        if not model_run_uuid:
            raise Site.DoesNotExist
    except Site.DoesNotExist:
        model_run_uuid = (
            AnnotationProposalSite.objects.filter(pk=evaluation_id)
            .values_list('annotation_proposal_set_uuid', flat=True)
            .first()
        )

    # Make sure site evaluation actually exists
    if not model_run_uuid:
        raise Http404()

    scalVal = params.scale
    if params.scale == 'custom':
        scalVal = params.scaleNum

    generate_site_images.delay(
        model_run_uuid,
        evaluation_id,
        params.constellation,
        params.force,
        params.dayRange,
        params.noData,
        params.overrideDates,
        scalVal,
        params.bboxScale,
        params.pointArea,
        params.worldviewSource,
    )
    return 202, True


@router.put(
    '/{evaluation_id}/cancel-generate-images/', response={202: bool, 409: str, 404: str}
)
def cancel_site_observation_images(request: HttpRequest, evaluation_id: UUID4):
    get_object_or_404(Site, pk=evaluation_id)

    with transaction.atomic():
        # Use select_for_update here to lock the SatelliteFetching row
        # for the duration of this transaction in order to ensure its
        # status doesn't change out from under us
        fetching_task = (
            SatelliteFetching.objects.select_for_update()
            .filter(site=evaluation_id)
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
