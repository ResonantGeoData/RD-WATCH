from datetime import datetime, timedelta
from typing import Any, Literal

from celery.result import AsyncResult
from ninja import Field, FilterSchema, Query, Schema
from ninja.errors import ValidationError
from ninja.pagination import PageNumberPagination, RouterPaginated, paginate
from ninja.schema import validator
from ninja.security import APIKeyHeader
from pydantic import UUID4, constr  # type: ignore

from django.conf import settings
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.core import signing
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import (
    Case,
    Count,
    Exists,
    F,
    Func,
    Max,
    Min,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    When,
)
from django.db.models.functions import Cast, Coalesce, JSONObject
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from rdwatch.core.db.functions import (
    AsGeoJSONDeserialized,
    BoundingBox,
    BoundingBoxGeoJSON,
    ExtractEpoch,
)
from rdwatch.core.models import (
    AnnotationExport,
    ModelRun,
    ModelRunUpload,
    Performer,
    Region,
    SatelliteFetching,
    SiteEvaluation,
)
from rdwatch.core.models.region import get_or_create_region
from rdwatch.core.schemas import RegionModel, SiteModel
from rdwatch.core.schemas.common import TimeRangeSchema
from rdwatch.core.tasks import (
    cancel_generate_images_task,
    download_annotations,
    generate_site_images_for_evaluation_run,
    process_model_run_upload_task,
)
from rdwatch.core.views.performer import PerformerSchema
from rdwatch.core.views.site_observation import GenerateImagesSchema

MODEL_RUN_PAGE_SIZE = 10

router = RouterPaginated()


class ModelRunAuth(APIKeyHeader):
    param_name = 'X-RDWATCH-API-KEY'

    def authenticate(self, request: HttpRequest, key: str | None) -> bool:
        return settings.MODEL_RUN_API_KEY == key


class ModelRunFilterSchema(FilterSchema):
    performer: list[str] | None
    region: str | None = Field(q='region__name')
    proposal: str | None = Field(q='proposal', ignore_none=False)
    groundtruth: bool | None

    def filter_performer(self, value: list[str] | None) -> Q:
        if value is None or not value:
            return Q()
        performer_q = Q()
        for performer_code in value:
            performer_q |= Q(performer__short_code=performer_code)
        return performer_q

    def filter_groundtruth(self, value: bool | None) -> Q:
        if value is None:
            return Q()
        # Filter for ground_truth performer
        if value:
            gt_q = Q(performer__short_code='TE')
            gt_q &= Q(ground_truth=value)
            return gt_q
        elif value is False:
            return Q(ground_truth=value)
        return Q()


class ModelRunWriteSchema(Schema):
    performer: str
    title: constr(max_length=1000)
    region: constr(min_length=1, max_length=255)
    parameters: dict
    expiration_time: int | None
    evaluation: int | None = None
    evaluation_run: int | None = None
    proposal: bool | None = None

    @validator('performer')
    def validate_performer(cls, v: str) -> Performer:
        try:
            return Performer.objects.get(short_code=v.upper())
        except Performer.DoesNotExist:
            raise ValueError(f"Invalid performer '{v}'")

    @validator('expiration_time')
    def validate_expiration_time(cls, v: int | None) -> timedelta | None:
        if v is not None:
            return timedelta(hours=v)
        return v


class ModelRunAdjudicated(Schema):
    proposed: int
    other: int
    ground_truths: str | None


class ModelRunDetailSchema(Schema):
    id: UUID4
    title: str
    eval: str | None = None
    region: str = Field(alias='region_name')
    performer: PerformerSchema
    parameters: dict
    numsites: int | None = Field(0, alias='cached_score')
    downloading: int | None = None
    score: float | None = Field(None, alias='cached_score')
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
    eval: str | None = None
    region: str = Field(..., alias='region_name')
    performer: PerformerSchema
    parameters: dict
    numsites: int | None = Field(0, alias='cached_numsites')
    downloading: int | None = None
    score: float | None = Field(None, alias='cached_score')
    timestamp: int | None = None
    timerange: TimeRangeSchema | None = None
    bbox: dict | None
    created: datetime
    expiration_time: timedelta | None = None
    evaluation: int | None = None
    evaluation_run: int | None = None
    proposal: str = None
    adjudicated: ModelRunAdjudicated | None = None
    groundTruthLink: UUID4 | None = None
    mode: Literal['batch', 'incremental'] | None = None


class ModelRunUploadSchema(Schema):
    title: str
    region: str | None = None
    performer: str | None = None
    zipfileKey: str
    private: bool = False


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
        ModelRun.objects.select_related('performer')
        # Order queryset so that ground truths are first
        .order_by('ground_truth', '-created').annotate(
            region_name=F('region__name'),
            downloading=Coalesce(
                Subquery(
                    SatelliteFetching.objects.filter(
                        site__configuration_id=OuterRef('pk'),
                        status=SatelliteFetching.Status.RUNNING,
                    )
                    .annotate(count=Func(F('id'), function='Count'))
                    .values('count')
                ),
                0,  # Default value when evaluations are None
            ),
            timestamp=ExtractEpoch('cached_timestamp'),
            timerange=JSONObject(
                min=ExtractEpoch('cached_timerange_min'),
                max=ExtractEpoch('cached_timerange_max'),
            ),
            bbox=AsGeoJSONDeserialized('cached_bbox'),
            groundTruthLink=Case(
                When(
                    Q(ground_truth=False),
                    then=Coalesce(
                        Subquery(
                            ModelRun.objects.filter(
                                ground_truth=True,
                                region_id=OuterRef('region_id'),
                                proposal=None,
                            )
                            .order_by('-created')
                            .values_list('pk')
                        ),
                        None,
                    ),
                ),
                # When not groundTruth we want to link the latest GroundTruth available
                # this is done for GroundTruth comparison on client-side
                When(
                    Q(ground_truth=True),
                    then=F('pk'),
                ),
                default=None,
            ),
            adjudicated=Case(
                When(
                    ~Q(proposal=None),  # When proposal has a value
                    then=JSONObject(
                        proposed=Coalesce(Subquery(proposed_count_subquery), 0),
                        other=Coalesce(Subquery(other_count_subquery), 0),
                        ground_truths=Subquery(
                            ModelRun.objects.filter(
                                ground_truth=True,
                                region_id=OuterRef('region_id'),
                                proposal=None,
                            )
                            .order_by('-created')
                            .values_list('pk')[:1]
                        ),
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
        qs = super().paginate_queryset(queryset, pagination, **params)
        aggregate_kwargs = {
            'timerange': JSONObject(
                min=ExtractEpoch(Min('evaluations__start_date')),
                max=ExtractEpoch(Max('evaluations__end_date')),
            ),
        }
        if filters.region:
            aggregate_kwargs['bbox'] = Coalesce(
                BoundingBoxGeoJSON('region__geom'),
                BoundingBoxGeoJSON('evaluations__geom'),
            )

        model_runs = qs | queryset.aggregate(**aggregate_kwargs)
        if filters.region:
            if qs['count'] == 0:  # No model runs; we set bbox to Region bbox
                region_filter = filters.dict()['region']
                # We do a full table scan because this isn't a common case and isn't a bottleneck;
                # the equivalent database query is really annoying due to the logic of the
                # `Region.value` property.
                for region in Region.objects.all():
                    if region.value == region_filter:
                        model_runs['bbox'] = region.geojson
                        break

        return model_runs


@router.post(
    '/',
    response={200: ModelRunDetailSchema},
    exclude_none=True,
    auth=[ModelRunAuth()],
)
# this is safe because we're using a nonstandard header w/ API Key for auth
@csrf_exempt
def create_model_run(
    request: HttpRequest,
    model_run_data: ModelRunWriteSchema,
):
    with transaction.atomic():
        region = get_or_create_region(model_run_data.region)[0]
        model_run = ModelRun.objects.create(
            title=model_run_data.title,
            performer=model_run_data.performer,
            region=region,
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
            'team_name': model_run.performer.team_name,
            'short_code': model_run.performer.short_code,
        },
        'region_name': region.name,
        'parameters': model_run.parameters,
        'numsites': 0,
        'created': model_run.created,
        'expiration_time': model_run.expiration_time,
    }


@router.get('/', response={200: list[ModelRunListSchema]})
@paginate(ModelRunPagination, page_size=MODEL_RUN_PAGE_SIZE)
def list_model_runs(
    request: HttpRequest,
    filters: ModelRunFilterSchema = Query(...),  # noqa: B008
):
    # TODO maybe the aggregate stats should have a separate endpoint since they only need to
    # be queried when the filters change, not every time a new page is loaded
    return filters.filter(get_queryset())


@router.post(
    '/{id}/finalization/',
    response={200: ModelRunDetailSchema},
    auth=[ModelRunAuth()],
)
# this is safe because we're using a nonstandard header w/ API Key for auth
@csrf_exempt
def finalize_model_run(request: HttpRequest, id: UUID4):
    model_run = get_object_or_404(ModelRun, pk=id)
    model_run.compute_aggregate_stats()
    return model_run


@router.get('/{id}/', response={200: ModelRunDetailSchema})
def get_model_run(request: HttpRequest, id: UUID4):
    return get_object_or_404(get_queryset(), id=id)


@router.get(
    '/api-key-version',
    response={200: list[ModelRunListSchema]},
    auth=[ModelRunAuth()],
)
@paginate(ModelRunPagination)
@csrf_exempt
def list_model_runs_api_key(
    request: HttpRequest,
    filters: ModelRunFilterSchema = Query(...),  # noqa: B008
):
    return filters.filter(get_queryset())


@router.post(
    '/{model_run_id}/site-model/',
    response={201: UUID4},
    auth=[ModelRunAuth()],
)
# this is safe because we're using a nonstandard header w/ API Key for auth
@csrf_exempt
def post_site_model(
    request: HttpRequest,
    model_run_id: UUID4,
    site_model: SiteModel,
):
    model_run = get_object_or_404(ModelRun, pk=model_run_id)
    site_evaluation = SiteEvaluation.bulk_create_from_site_model(site_model, model_run)
    return 201, site_evaluation.id


# Utilized in the client editor for adding new site-models
@router.post(
    '/{model_run_id}/editor/site-model/',
    response={201: UUID4},
)
def post_site_model_editor(
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
    auth=[ModelRunAuth()],
)
# this is safe because we're using a nonstandard header w/ API Key for auth
@csrf_exempt
def post_region_model(
    request: HttpRequest,
    model_run_id: UUID4,
    region_model: RegionModel,
):
    model_run = get_object_or_404(ModelRun, pk=model_run_id)
    site_evaluations = SiteEvaluation.bulk_create_from_region_model(
        region_model, model_run
    )
    return 201, [eval.id for eval in site_evaluations]


# Utilized in the client editor for adding new region-models
@router.post(
    '/{model_run_id}/editor/region-model/',
    response={201: list[UUID4]},
)
def post_region_model_editor(
    request: HttpRequest,
    model_run_id: UUID4,
    region_model: RegionModel,
):
    model_run = get_object_or_404(ModelRun, pk=model_run_id)
    site_evaluations = SiteEvaluation.bulk_create_from_region_model(
        region_model, model_run
    )
    return 201, [eval.id for eval in site_evaluations]


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
        params.pointArea,
        params.worldviewSource,
    )
    return 202, True


@router.put(
    '/{model_run_id}/cancel-generate-images/',
    response={202: bool, 409: str, 404: str},
)
def cancel_generate_images(request: HttpRequest, model_run_id: UUID4):
    get_object_or_404(ModelRun, id=model_run_id)  # existence check

    cancel_generate_images_task.delay(model_run_id)

    return 202, True


def get_model_run_details(model_run_id: UUID4):
    return (
        ModelRun.objects.filter(pk=model_run_id)
        .alias(version=F('evaluations__version'))
        .annotate(
            json=JSONObject(
                region=F('region__name'),
                performer=JSONObject(
                    id=F('performer__id'),
                    team_name=F('performer__team_name'),
                    short_code=F('performer__short_code'),
                ),
                version=F('version'),
                proposal=F('proposal'),
                title=F('title'),
            ),
        )
    )


def get_sites_query(model_run_id: UUID4):
    return (
        SiteEvaluation.objects.select_related('siteimage', 'satellite_fetching')
        .filter(configuration=model_run_id)
        .annotate(
            siteimage_count=Count('siteimage'),
            S2=Count(Case(When(siteimage__source='S2', then=1))),
            WV=Count(Case(When(siteimage__source='WV', then=1))),
            L8=Count(Case(When(siteimage__source='L8', then=1))),
            PL=Count(Case(When(siteimage__source='PL', then=1))),
            time=ExtractEpoch('timestamp'),
            site_id=F('id'),
            transformed_geom=Transform('geom', 4326),
            transformed_point=Transform('point', 4326),
            geom_or_point=Coalesce(
                Cast('transformed_geom', GeometryField()),
                Cast('transformed_point', GeometryField()),
            ),
            downloading=Exists(
                SatelliteFetching.objects.filter(
                    site=OuterRef('pk'),
                    status=SatelliteFetching.Status.RUNNING,
                )
            ),
        )
        .aggregate(
            sites=JSONBAgg(
                JSONObject(
                    id='pk',
                    timestamp='time',
                    number='number',
                    bbox=BoundingBox('geom_or_point'),
                    images='siteimage_count',
                    S2='S2',
                    WV='WV',
                    L8='L8',
                    start_date=ExtractEpoch('start_date'),
                    end_date=ExtractEpoch('end_date'),
                    status='status',
                    filename='cache_originator_file',
                    downloading='downloading',
                    groundtruth=F('configuration__ground_truth'),
                ),
                ordering='number',
                default=[],
            ),
        )
    )


@router.get('/{model_run_id}/proposals/')
def get_proposals(request: HttpRequest, model_run_id: UUID4):
    data = get_model_run_details(model_run_id).values_list('json', flat=True)
    if not data.exists():
        raise Http404()

    query = get_sites_query(model_run_id)
    model_run = data.first()
    query['region'] = model_run['region']
    query['modelRunDetails'] = model_run
    return 200, query


@router.get('/{model_run_id}/sites/')
def get_sites(request: HttpRequest, model_run_id: UUID4):
    data = get_model_run_details(model_run_id).values_list('json', flat=True)
    if not data.exists():
        raise Http404()

    query = get_sites_query(model_run_id)
    model_run = data[0]
    query['region'] = model_run['region']
    query['modelRunDetails'] = model_run
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


@router.get('/download_status/{task_id}')
def check_download(request: HttpRequest, task_id: UUID4):
    task = AsyncResult(task_id)
    return task.status


@router.get('/{id}/download/{task_id}/')
def get_downloaded_annotations(request: HttpRequest, id: UUID4, task_id: str):
    annotation_export = AnnotationExport.objects.filter(
        configuration=id, celery_id=task_id
    )
    if annotation_export.exists():
        annotation_export = annotation_export.first()
        response = HttpResponse(
            annotation_export.export_file.file, content_type='application/zip'
        )
        response[
            'Content-Disposition'
        ] = f'attachment; filename="{annotation_export.name}.zip"'
        return response


@router.post('/start_upload_processing')
def start_model_run_upload_processing(
    request: HttpRequest, upload_data: ModelRunUploadSchema
):
    zipfile_upload = signing.loads(upload_data.zipfileKey)

    with transaction.atomic():
        upload = ModelRunUpload.objects.create(
            title=upload_data.title.strip(),
            region=upload_data.region.strip(),
            performer=upload_data.performer.strip(),
            zipfile=zipfile_upload['object_key'],
            private=upload_data.private,
        )
        if not upload.title:
            raise ValidationError('Invalid model run title')
        if not default_storage.exists(upload.zipfile.name):
            raise ValidationError('Invalid file name provided')
        upload.save()

    task = process_model_run_upload_task.delay(upload.id)
    return task.id


@router.get('/upload_status/{task_id}')
def model_run_upload_status(request: HttpRequest, task_id: str):
    result = AsyncResult(task_id)
    return {
        'status': result.status,
        'traceback': result.traceback,
    }
