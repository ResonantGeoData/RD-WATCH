import logging
from typing import Literal, TypeAlias

from ninja import FilterSchema, Query
from ninja.pagination import RouterPaginated
from pydantic import UUID4

from django.db.models import (
    Avg,
    CharField,
    Count,
    DateTimeField,
    F,
    FloatField,
    Func,
    JSONField,
    Max,
    Min,
    Q,
    Value,
)
from django.db.models.functions import Concat, JSONObject, NullIf
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.db.functions import ExtractEpoch
from rdwatch.views.model_run import ModelRunDetailSchema, ModelRunPagination
from rdwatch_scoring.models import EvaluationRun, SatelliteFetching
from rdwatch_scoring.tasks import (
    cancel_generate_images_task,
    generate_site_images_for_evaluation_run,
)
from rdwatch_scoring.views.observation import GenerateImagesSchema

logger = logging.getLogger(__name__)

router = RouterPaginated()

Mode: TypeAlias = Literal['batch', 'incremental']


class ModelRunFilterSchema(FilterSchema):
    performer: list[str] | None
    region: str | None
    eval: list[str] | None
    # proposal: str | None = Field(q='proposal', ignore_none=False)
    mode: list[Mode] | None

    def filter_performer(self, value: list[str] | None) -> Q:
        if value is None or not value:
            return Q()
        performer_q = Q()
        for performer_slug in value:
            performer_q |= Q(performer=performer_slug)
        return performer_q

    def filter_mode(self, value: list[Mode] | None) -> Q:
        if value is None or not value:
            return Q()
        mode_q = Q()
        for mode in value:
            mode_q |= Q(mode=mode)
        return mode_q

    def filter_eval(self, value: list[str] | None) -> Q:
        if value is None or not value:
            return Q()
        eval_q = Q()
        for eval in value:
            eval_num = eval.split('.')[0]
            eval_run_num = eval.split('.')[1]
            eval_q |= Q(evaluation_number=eval_num, evaluation_run_number=eval_run_num)
        return eval_q


def get_queryset():
    return (
        EvaluationRun.objects.filter(
            evaluationbroadareasearchmetric__activity_type='overall',
            evaluationbroadareasearchmetric__tau=0.2,
            evaluationbroadareasearchmetric__rho=0.5,
        )
        .values()
        .annotate(
            id=F('uuid'),
            title=Concat(
                Value('Eval '),
                'evaluation_number',
                Value('.'),
                'evaluation_run_number',
                Value('.'),
                'evaluation_increment_number',
                Value(' '),
                'performer',
                output_field=CharField(),
            ),
            eval=Concat(
                'evaluation_number',
                Value('.'),
                'evaluation_run_number',
                output_field=CharField(),
            ),
            region=F('region'),
            performer_slug=F('performer'),
            performer=JSONObject(
                id=0, team_name=F('performer'), short_code=F('performer')
            ),
            parameters=Value({}, output_field=JSONField()),
            numsites=F('evaluationbroadareasearchmetric__proposed_sites'),
            downloading=Value(0),
            score=Avg(
                NullIf(
                    'site__confidence_score', Value('NaN'), output_field=FloatField()
                )
            ),
            timestamp=ExtractEpoch(Max('site__end_date')),
            timerange=JSONObject(
                min=ExtractEpoch(Min('site__start_date')),
                max=ExtractEpoch(Max('site__end_date')),
            ),
            # bbox=Value({}, output_field=JSONField()),
            bbox=Func(
                F('site__region__geometry'),
                4326,
                function='ST_AsGeoJSON',
                output_field=JSONField(),
            ),
            created=F('start_datetime'),
            expiration_time=Value(None, output_field=DateTimeField()),
            evaluation=F('evaluation_number'),
            evaluation_run=F('evaluation_run_number'),
            proposal=Value(None, output_field=CharField()),
            adjudicated=JSONObject(
                proposed=0,
                other=0,
            ),
        )
    )


@router.get('/', response={200: ModelRunPagination.Output})
def list_model_runs(
    request: HttpRequest,
    filters: ModelRunFilterSchema = Query(...),  # noqa: B008
):
    page_size: int = 10  # TODO: use settings.NINJA_PAGINATION_PER_PAGE?
    page = int(request.GET.get('page', 1))

    qs = filters.filter(
        EvaluationRun.objects.all().order_by(
            F('region'),
            F('performer'),
            F('evaluation_number'),
            F('evaluation_run_number'),
            F('evaluation_increment_number'),
        )
    )

    ids = qs[((page - 1) * page_size) : (page * page_size)].values_list(
        'uuid', flat=True
    )
    total_count = qs.count()

    qs = (
        EvaluationRun.objects.filter(
            uuid__in=ids,
            evaluationbroadareasearchmetric__activity_type='overall',
            evaluationbroadareasearchmetric__tau=0.2,
            evaluationbroadareasearchmetric__rho=0.5,
        )
        .values()
        .annotate(
            id=F('uuid'),
            title=Concat(
                Value('Eval '),
                'evaluation_number',
                Value('.'),
                'evaluation_run_number',
                Value('.'),
                'evaluation_increment_number',
                Value(' '),
                'performer',
                output_field=CharField(),
            ),
            eval=Concat(
                'evaluation_number',
                Value('.'),
                'evaluation_run_number',
                output_field=CharField(),
            ),
            performer=JSONObject(
                id=0, team_name=F('performer'), short_code=F('performer')
            ),
            parameters=Value({}, output_field=JSONField()),
            created=F('start_datetime'),
            expiration_time=Value(None, output_field=DateTimeField()),
            evaluation=F('evaluation_number'),
            evaluation_run=F('evaluation_run_number'),
            proposal=Value(None, output_field=CharField()),
            adjudicated=JSONObject(
                proposed=0,
                other=0,
            ),
            score=Avg(
                NullIf(
                    'site__confidence_score', Value('NaN'), output_field=FloatField()
                )
            ),
            numsites=F('evaluationbroadareasearchmetric__proposed_sites'),
            timestamp=ExtractEpoch(Max('site__end_date')),
            timerange=JSONObject(
                min=ExtractEpoch(Min('site__start_date')),
                max=ExtractEpoch(Max('site__end_date')),
            ),
            bbox=Func(
                F('site__region__geometry'),
                4326,
                function='ST_AsGeoJSON',
                output_field=JSONField(),
            ),
        )
    ).order_by(
        F('region'),
        F('performer'),
        F('evaluation_number'),
        F('evaluation_run_number'),
        F('evaluation_increment_number'),
    )

    aggregate_kwargs = {
        'timerange': JSONObject(
            min=ExtractEpoch(Min('site__start_date')),
            max=ExtractEpoch(Max('site__end_date')),
        ),
    }
    if filters.region:
        aggregate_kwargs['bbox'] = Max(
            Func(
                F('site__region__geometry'),
                4326,
                function='ST_AsGeoJSON',
                output_field=JSONField(),
            )
        )

    model_runs = {
        'items': list(qs),
        'count': total_count,
        **qs.aggregate(**aggregate_kwargs),
    }

    fetch_counts = (
        SatelliteFetching.objects.filter(status=SatelliteFetching.Status.RUNNING)
        .values('model_run_uuid')
        .order_by('model_run_uuid')
        .annotate(total=Count('model_run_uuid'))
    )
    # convert it into a dictionary for easy indexing
    fetching = {}
    for item in fetch_counts:
        if item['model_run_uuid']:
            fetching[item['model_run_uuid']] = item['total']

    for item in model_runs['items']:
        if item['uuid'] in fetching.keys():
            item['downloading'] = fetching[item['uuid']]

    return model_runs


@router.get('/{id}/', response={200: ModelRunDetailSchema})
def get_model_run(request: HttpRequest, id: UUID4):
    data = get_object_or_404(get_queryset(), id=id)
    fetch_counts = SatelliteFetching.objects.filter(
        model_run_uuid=id, status=SatelliteFetching.Status.RUNNING
    ).count()
    data['downloading'] = fetch_counts
    return data


@router.post('/{model_run_id}/generate-images/', response={202: bool})
def generate_images(
    request: HttpRequest,
    model_run_id: UUID4,
    params: GenerateImagesSchema = Query(...),  # noqa: B008
):
    scalVal = params.scale
    if params.scale == 'custom':
        scalVal = params.scaleNum
    generate_site_images_for_evaluation_run(
        model_run_id,
        params.constellation,
        params.force,
        params.dayRange,
        params.noData,
        params.overrideDates,
        scalVal,
        params.bboxScale,
    )
    return 202, True


@router.put(
    '/{model_run_id}/cancel-generate-images/',
    response={202: bool, 409: str, 404: str},
)
def cancel_generate_images(request: HttpRequest, model_run_id: UUID4):
    get_object_or_404(EvaluationRun, uuid=model_run_id)  # existence check

    cancel_generate_images_task.delay(model_run_id)

    return 202, True
