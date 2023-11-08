from datetime import timedelta
from typing import Any

from celery.result import AsyncResult
from ninja import Field, FilterSchema, Query, Schema
from ninja.pagination import PageNumberPagination, RouterPaginated, paginate
from pydantic import UUID4

from django.core.cache import cache
from django.db import transaction
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
    QuerySet,
    Value,
)
from django.db.models.functions import Concat, JSONObject, NullIf
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.db.functions import ExtractEpoch
from rdwatch.schemas.common import TimeRangeSchema
from rdwatch.views.model_run import ModelRunDetailSchema, ModelRunListSchema
from rdwatch_scoring.models import EvaluationRun, SatelliteFetching, Site
from rdwatch_scoring.views.observation import (
    GenerateImagesSchema,
    get_site_observation_images,
)

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


def get_queryset():
    return EvaluationRun.objects.values().annotate(
        id=F('uuid'),
        title=Concat(
            Value('Eval '),
            'evaluation_number',
            Value('.'),
            'evaluation_run_number',
            Value(' '),
            'performer',
            output_field=CharField(),
        ),
        region=F('region'),
        performer_slug=F('performer'),
        performer=JSONObject(id=0, team_name=F('performer'), short_code=F('performer')),
        parameters=Value({}, output_field=JSONField()),
        numsites=Count('site__uuid'),
        downloading=Value(0),
        score=Avg(
            NullIf('site__confidence_score', Value('NaN'), output_field=FloatField())
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
                aggregate_kwargs['bbox'] = Max(
                    Func(
                        F('site__region__geometry'),
                        4326,
                        function='ST_AsGeoJSON',
                        output_field=JSONField(),
                    )
                )

            model_runs = qs | queryset.aggregate(**aggregate_kwargs)
            cache.set(
                key=cache_key,
                value=model_runs,
                timeout=timedelta(days=30).total_seconds(),
            )

        return model_runs


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


@router.get('/{id}/', response={200: ModelRunDetailSchema})
def get_model_run(request: HttpRequest, id: UUID4):
    return get_object_or_404(get_queryset(), id=id)


@router.post('/{model_run_id}/generate-images/', response={202: bool})
def generate_images(
    request: HttpRequest,
    model_run_id: UUID4,
    params: GenerateImagesSchema = Query(...),  # noqa: B008
):
    sites = Site.objects.filter(evaluation_run_uuid=model_run_id)
    for site in sites:
        get_site_observation_images(
            request,
            site.pk,
            params,
        )

    return 202, True


@router.put(
    '/{model_run_id}/cancel-generate-images/',
    response={202: bool, 409: str, 404: str},
)
def cancel_generate_images(request: HttpRequest, model_run_id: UUID4):
    sites = Site.objects.filter(evaluation_run_uuid=model_run_id)

    for site in sites:
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

    return 202, True
