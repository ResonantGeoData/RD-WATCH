from datetime import datetime, timedelta
from typing import Any, Literal

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
    Count,
    F,
    Func,
    JSONField,
    Max,
    Min,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    When,
)
from django.db.models.functions import Coalesce, JSONObject
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.db.functions import BoundingBox, BoundingBoxGeoJSON, ExtractEpoch
from rdwatch.models import (
    AnnotationExport,
    ModelRun,
    Region,
    SatelliteFetching,
    SiteEvaluation,
    lookups,
)
from rdwatch.schemas import RegionModel, SiteModel
from rdwatch.schemas.common import TimeRangeSchema
from rdwatch.tasks import download_annotations
from rdwatch.views.performer import PerformerSchema
from rdwatch.views.site_observation import get_site_observation_images

router = RouterPaginated()


class ModelRunFilterSchema(FilterSchema):
    performer: list[str] | None = Field(q='performer_slug')
    region: str | None
    proposal: str | None = Field(q='proposal', ignore_none=False)

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
    def validate_performer(cls, v: str) -> lookups.Performer:
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
    # Subquery to count unique SiteEvaluations
    # with proposal='PROPOSAL' for each ModelRun
    proposed_count_subquery = (
        SiteEvaluation.objects.filter(
            configuration=OuterRef('pk'),
            status='PROPOSAL',
        )
        .values('configuration')
        .annotate(count=Count('pk'))
        .values('count')
    )

    # Subquery to count unique SiteEvaluations with proposal
    # not equal to 'PROPOSAL' for each ModelRun
    other_count_subquery = (
        SiteEvaluation.objects.filter(configuration=OuterRef('pk'))
        .exclude(status='PROPOSAL')
        .values('configuration')
        .annotate(count=Count('pk'))
        .values('count')
    )

    return (
        ModelRun.objects
        # Get minimum score and performer so that we can tell which runs
        # are ground truth
        .annotate(
            min_score=Min('evaluations__score'), performer_slug=F('performer__slug')
        )
        # Label ground truths as such. A ground truth is defined as a model run
        # with a min_score of 1 and a performer of "TE"
        .alias(
            groundtruth=Case(
                When(min_score=1, performer_slug__iexact='TE', then=True),
                default=False,
            )
        )
        # Order queryset so that ground truths are first
        .order_by('-groundtruth', '-id')
        .alias(
            region_id=F('evaluations__region_id'),
            evaluation_configuration=F('evaluations__configuration'),
            proposal_val=F('proposal'),
        )
        .values()
        .annotate(
            performer=Subquery(  # prevents including "performer" in slow GROUP BY
                lookups.Performer.objects.filter(pk=OuterRef('performer_id')).values(
                    json=JSONObject(
                        id='id',
                        team_name='description',
                        short_code='slug',
                    )
                ),
                output_field=JSONField(),
            ),
            region=Subquery(  # prevents including "region" in slow GROUP BY
                Region.objects.filter(pk=OuterRef('region_id')).values('name')[:1],
            ),
            downloading=Coalesce(
                Subquery(
                    SatelliteFetching.objects.filter(
                        siteeval__configuration_id=OuterRef('evaluation_configuration'),
                        status=SatelliteFetching.Status.RUNNING,
                    )
                    .annotate(count=Func(F('id'), function='Count'))
                    .values('count')
                ),
                0,  # Default value when evaluations are None
            ),
            numsites=Count('evaluations__pk', distinct=True),
            score=Avg('evaluations__score'),
            timestamp=ExtractEpoch(Max('evaluations__timestamp')),
            timerange=JSONObject(
                min=ExtractEpoch(Min('evaluations__start_date')),
                max=ExtractEpoch(Max('evaluations__end_date')),
            ),
            bbox=BoundingBoxGeoJSON('evaluations__geom'),
            adjudicated=Case(
                When(
                    ~Q(proposal_val=None),  # When proposal has a value
                    then=JSONObject(
                        proposed=Coalesce(Subquery(proposed_count_subquery), 0),
                        other=Coalesce(Subquery(other_count_subquery), 0),
                    ),
                ),
                default=None,
            ),
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
                    min=ExtractEpoch(Min('evaluations__start_date')),
                    max=ExtractEpoch(Max('evaluations__end_date')),
                ),
            }
            if filters.region:
                aggregate_kwargs['bbox'] = Coalesce(
                    BoundingBoxGeoJSON('evaluations__region__geom'),
                    BoundingBoxGeoJSON('evaluations__geom'),
                )

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
    most_recent_evaluation = ModelRun.objects.aggregate(
        latest_eval=Max('evaluations__timestamp')
    )['latest_eval']

    return '|'.join(
        [
            ModelRun.__name__,
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


@router.post(
    '/{model_run_id}/site-model/',
    response={201: UUID4},
)
def post_site_model(
    request: HttpRequest,
    model_run_id: UUID4,
    site_model: SiteModel,
):
    model_run = get_object_or_404(ModelRun, pk=model_run_id)
    site_evaluation = SiteEvaluation.bulk_create_from_site_model(site_model, model_run)
    return 201, site_evaluation.id


@router.post(
    '/{model_run_id}/region-model/',
    response={201: list[UUID4]},
)
def post_region_model(
    request: HttpRequest,
    model_run_id: UUID4,
    region_model: RegionModel,
):
    model_run = get_object_or_404(ModelRun, pk=model_run_id)
    site_evaluations = SiteEvaluation.bulk_create_from_from_region_model(
        region_model, model_run
    )
    return 201, [eval.id for eval in site_evaluations]


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
    siteEvaluations = SiteEvaluation.objects.filter(configuration=model_run_id)

    for eval in siteEvaluations:
        get_site_observation_images(
            request,
            eval.pk,
            constellation,
            dayRange,
            noData,
            overrideDates,
            force,
            scale,
        )

    return 202, True


@router.put(
    '/{model_run_id}/cancel-generate-images/',
    response={202: bool, 409: str, 404: str},
)
def cancel_generate_images(request: HttpRequest, model_run_id: UUID4):
    siteEvaluations = SiteEvaluation.objects.filter(configuration=model_run_id)

    for eval in siteEvaluations:
        with transaction.atomic():
            # Use select_for_update here to lock the SatelliteFetching row
            # for the duration of this transaction in order to ensure its
            # status doesn't change out from under us
            fetching_task = (
                SatelliteFetching.objects.select_for_update()
                .filter(siteeval=eval.pk)
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
    return (
        SiteEvaluation.objects.select_related('siteimage')
        .filter(configuration=model_run_id)
        .annotate(
            siteimage_count=Count('siteimage'),
            S2=Count(Case(When(siteimage__source='S2', then=1))),
            WV=Count(Case(When(siteimage__source='WV', then=1))),
            L8=Count(Case(When(siteimage__source='L8', then=1))),
            time=ExtractEpoch('timestamp'),
        )
        .aggregate(
            evaluations=JSONBAgg(
                JSONObject(
                    id='pk',
                    timestamp='time',
                    number='number',
                    bbox=BoundingBox('geom'),
                    images='siteimage_count',
                    S2='S2',
                    WV='WV',
                    L8='L8',
                    start_date=ExtractEpoch('start_date'),
                    end_date=ExtractEpoch('end_date'),
                    status='status',
                    filename='cache_originator_file',
                ),
                ordering='number',
            ),
        )
    )


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
def get_downloaded_annotations(request: HttpRequest, id: str, task_id: str):
    annotation_export = AnnotationExport.objects.filter(celery_id=task_id)
    if annotation_export.exists():
        annotation_export = annotation_export.first()
        response = HttpResponse(
            annotation_export.export_file.file, content_type='application/zip'
        )
        response[
            'Content-Disposition'
        ] = f'attachment; filename="{annotation_export.name}.zip"'
        return response
