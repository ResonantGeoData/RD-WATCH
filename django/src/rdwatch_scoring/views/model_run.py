from datetime import datetime, timedelta
from typing import Any, Literal

import json
import geojson
from shapely.wkt import loads
from shapely.geometry import mapping

from celery.result import AsyncResult
from ninja import Field, FilterSchema, Query, Schema
from ninja.pagination import PageNumberPagination, RouterPaginated, paginate
from ninja.schema import validator
from pydantic import UUID4, constr  # type: ignore

from django.contrib.postgres.aggregates import JSONBAgg
from django.core.cache import cache
from django.db import transaction
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    DateTimeField,
    ExpressionWrapper,
    F,
    FloatField,
    Func,
    IntegerField,
    JSONField,
    Max,
    Min,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    When,
    Value,
)
from django.db.models.functions import Coalesce, JSONObject, Concat, NullIf
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.db.functions import BoundingBox, BoundingBoxGeoJSON, ExtractEpoch
from rdwatch_scoring.models import (
    EvaluationBroadAreaSearchMetric,
    EvaluationRun,
    ModelRun,
    Performer,
    Region,
    Site,
    SiteEvaluation,
    lookups,
)
from rdwatch.schemas.common import TimeRangeSchema
from rdwatch.tasks import download_annotations
from rdwatch_scoring.views.performer import PerformerSchema

router = RouterPaginated()


class ModelRunFilterSchema(FilterSchema):
    performer: list[str] | None = Field(q='performer_slug')
    region: str | None
    # proposal: str | None = Field(q='proposal', ignore_none=False)

    def filter_performer(self, value: list[str] | None) -> Q:
        if value is None or not value:
            return Q()
        performer_q = Q()
        for performer_slug in value:
            performer_q |= Q(performer_slug=performer_slug)
        return performer_q


class ModelRunWriteSchema(Schema):
    performer: str
    title: constr(max_length=1000)
    parameters: dict
    expiration_time: int | None
    evaluation: int | None = None
    evaluation_run: int | None = None
    proposal: bool | None = None

    @validator('performer')
    def validate_performer(cls, v: str) -> Performer:
        try:
            return lookups.Performer.objects.get(slug=v.upper())
        except lookups.Performer.DoesNotExist:
            raise ValueError(f"Invalid performer '{v}'")

    @validator('expiration_time')
    def validate_expiration_time(cls, v: int | None) -> timedelta | None:
        if v is not None:
            return timedelta(hours=v)
        return v


class ModelRunAdjudicated(Schema):
    proposed: int
    other: int


class ModelRunDetailSchema(Schema):
    id: UUID4
    title: str
    region: str | None = None
    performer: PerformerSchema
    parameters: dict
    numsites: int
    downloading: int | None = None
    score: float | None = None
    timestamp: int | None = None
    timerange: TimeRangeSchema | None = None
    bbox: dict | None
    created: datetime
    expiration_time: timedelta | None = None
    evaluation: int | None = None
    evaluation_run: int | None = None
    proposal: str = None
    adjudicated: ModelRunAdjudicated | None = None


class ModelRunListSchema(Schema):
    id: UUID4
    title: str
    region: str | None = None
    performer: PerformerSchema
    parameters: dict
    numsites: int
    downloading: int | None = None
    score: float | None = None
    timestamp: int | None = None
    timerange: TimeRangeSchema | None = None
    bbox: dict | None
    created: datetime
    expiration_time: timedelta | None = None
    evaluation: int | None = None
    evaluation_run: int | None = None
    proposal: str = None
    adjudicated: ModelRunAdjudicated | None = None


def get_queryset():
    return (EvaluationRun.objects
        .filter(region__in=['AE_R001', 'BR_R002', 'KR_R002'], evaluation_run_number=0, mode='batch')
        .values()
        .annotate(
            id=F('uuid'),
            title=Concat(
                Value('Eval '),
                'evaluation_number',
                Value('.'),
                'evaluation_run_number',
                Value(' '),
                'performer',
                output_field=CharField()
            ),
            region=F('region'),
            performer_slug=F('performer'),
            performer=JSONObject(
                id=0,
                team_name=F('performer'),
                short_code=F('performer')
            ),
            parameters=Value({}, output_field=JSONField()),
            numsites=Count('site__uuid'),
            downloading=Value(0),
            score=Avg(NullIf('site__confidence_score', Value('NaN'), output_field=FloatField())),
            timestamp=ExtractEpoch(Max('site__end_date')),
            timerange=JSONObject(
                min=ExtractEpoch(Min('site__start_date')),
                max=ExtractEpoch(Max('site__end_date'))
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
            )
        )
    )


class ModelRunPagination(PageNumberPagination):
    class Output(Schema):
        count: int
        timerange: TimeRangeSchema | None = None
        bbox: dict | None = None
        items: list[ModelRunListSchema]

    def paginate_queryset(
        self,
        queryset: QuerySet,
        pagination: PageNumberPagination.Input,
        filters: ModelRunFilterSchema,
        **params,
    ) -> dict[str, Any]:
        # TODO: remove caching after model runs endpoint is
        # refactored to be more efficient.
        cache_key = _get_model_runs_cache_key(filters.dict())
        model_runs = cache.get(cache_key)

        # If we have a cache miss, execute the query and save the results to cache
        # before returning.
        if model_runs is None:
            qs = super().paginate_queryset(queryset, pagination, **params)

            aggregate_kwargs = {
                'timerange': JSONObject(
                    min=ExtractEpoch(Min('site__start_date')),
                    max=ExtractEpoch(Max('site__end_date')),
                ),
            }
            if filters.region:
                aggregate_kwargs['bbox'] = Max(Func(
                    F('site__region__geometry'),
                    4326,
                    function='ST_AsGeoJSON',
                    output_field=JSONField(),
                ))

            model_runs = qs | queryset.aggregate(**aggregate_kwargs)
            cache.set(
                key=cache_key,
                value=model_runs,
                timeout=timedelta(days=30).total_seconds(),
            )

        return model_runs


@router.post('/', response={200: ModelRunDetailSchema}, exclude_none=True)
def create_model_run(
    request: HttpRequest,
    model_run_data: ModelRunWriteSchema,
):
    model_run = ModelRun.objects.create(
        title=model_run_data.title,
        performer=model_run_data.performer,
        parameters=model_run_data.parameters,
        expiration_time=model_run_data.expiration_time,
        evaluation=model_run_data.evaluation,
        evaluation_run=model_run_data.evaluation_run,
        proposal=model_run_data.proposal,
    )
    return 200, {
        'id': model_run.pk,
        'title': model_run.title,
        'performer': {
            'id': model_run.performer.pk,
            'team_name': model_run.performer.description,
            'short_code': model_run.performer.slug,
        },
        'parameters': model_run.parameters,
        'numsites': 0,
        'created': model_run.created,
        'expiration_time': model_run.expiration_time,
    }


def _get_model_runs_cache_key(params: dict) -> str:
    """Generate a cache key for the model runs listing endpoint."""
    most_recent_evaluation = EvaluationRun.objects.aggregate(
        latest_eval=Max('start_datetime')
    )['latest_eval']

    return '|'.join(
        [
            EvaluationRun.__name__,
            str(most_recent_evaluation),
            *[f'{key}={value}' for key, value in params.items()],
        ]
    ).replace(' ', '_')


@router.get('/', response={200: list[ModelRunListSchema]})
@paginate(ModelRunPagination)
def list_model_runs(
    request: HttpRequest,
    filters: ModelRunFilterSchema = Query(...),  # noqa: B008
):
    return filters.filter(get_queryset())
    # return get_queryset()



@router.get('/{id}/', response={200: ModelRunDetailSchema})
def get_model_run(request: HttpRequest, id: UUID4):
    return get_object_or_404(get_queryset(), id=id)


@router.post('/{model_run_id}/generate-images/', response={202: bool})
def generate_images(
    request: HttpRequest,
    model_run_id: UUID4,
    constellation: Literal['WV', 'S2', 'L8'] = 'WV',
    dayRange: int = 14,
    noData: int = 50,
    overrideDates: None | list[str] = None,
    force: bool = False,
    scale: str = 'default',
):
    # TODO

    return 202, True


@router.put(
    '/{model_run_id}/cancel-generate-images/',
    response={202: bool, 409: str, 404: str},
)
def cancel_generate_images(request: HttpRequest, model_run_id: UUID4):
    # TODO
    return 202, True


def get_region(model_run_id: UUID4):
    return (
        ModelRun.objects.select_related('evaluations')
        .filter(pk=model_run_id)
        .alias(
            region_id=F('evaluations__region_id'),
        )
        .annotate(
            json=JSONObject(
                region=Subquery(  # prevents including "region" in slow GROUP BY
                    Region.objects.filter(pk=OuterRef('region_id')).values('name')[:1],
                    output_field=JSONField(),
                ),
            ),
        )
    )


def get_evaluations_query(model_run_id: UUID4):
    # TODO
    return None


@router.get('/{model_run_id}/evaluations')
def get_modelrun_evaluations(request: HttpRequest, model_run_id: UUID4):
    region = get_region(model_run_id).values_list('json', flat=True)
    if not region.exists():
        raise Http404()

    query = get_evaluations_query(model_run_id)
    model_run = region[0]
    query['region'] = model_run['region']
    return 200, query


@router.post('/{id}/download/')
def start_download(
    request: HttpRequest,
    id: UUID4,
    mode: Literal['all', 'approved', 'rejected'] = 'all',
):
    task_id = download_annotations.delay(id, mode)
    print(task_id)
    return task_id.id


@router.get('/download_status')
def check_download(request: HttpRequest, task_id: str):
    task = AsyncResult(task_id)
    print(task)
    return task.status


@router.get('/{id}/download')
def get_downloaded_annotations(request: HttpRequest, id: int, task_id: str):
    # TODO
    return None
