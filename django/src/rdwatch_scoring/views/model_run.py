import logging
from typing import Literal, TypeAlias

from ninja import Field, FilterSchema, Query
from ninja.pagination import RouterPaginated
from pydantic import UUID4

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    DateTimeField,
    Exists,
    F,
    FloatField,
    Func,
    IntegerField,
    JSONField,
    Max,
    Min,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Concat, JSONObject, NullIf, Substr
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404


from rdwatch.db.functions import ExtractEpoch
from rdwatch.db.functions import BoundingBox, BoundingBoxGeoJSON, ExtractEpoch
from rdwatch.views.model_run import ModelRunDetailSchema, ModelRunPagination
from rdwatch_scoring.models import EvaluationRun, SatelliteFetching, AnnotationProposalSet, AnnotationProposalSite, \
    AnnotationProposalObservation, Region, SiteImage
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
            evaluationbroadareasearchmetric__min_confidence_score=0.0,
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


def get_queryset_proposal():
    return (
        AnnotationProposalSet.objects.values()
        .annotate(
            id=F('uuid'),
            region=F('region_id'),
            title=Concat(
                Value('Proposal '),
                'originator',
                Value(' '),
                'region_id',
                output_field=CharField(),
            ),
            eval=Value(None, output_field=CharField()),
            performer=JSONObject(
                id=0, team_name=F('originator'), short_code=F('originator')
            ),
            parameters=Value({}, output_field=JSONField()),
            created=F('create_datetime'),
            expiration_time=Value(None, output_field=DateTimeField()),
            evaluation=Value(None, output_field=DateTimeField()),
            evaluation_run=Value(None, output_field=DateTimeField()),
            proposal=Value(None, output_field=CharField()),
            adjudicated=JSONObject(
                proposed=0,
                other=0,
            ),
            score=Value(None, output_field=FloatField()),
            numsites=Count('annotationproposalsite'),
            timestamp=ExtractEpoch(Max('annotationproposalsite__end_date')),
            timerange=JSONObject(
                min=ExtractEpoch(Min('annotationproposalsite__start_date')),
                max=ExtractEpoch(Max('annotationproposalsite__end_date')),
            ),
            bbox=Func(
                F('region_id__geometry'),
                4326,
                function='ST_AsGeoJSON',
                output_field=JSONField(),
            ),
        )
    ).order_by(
        F('uuid')
    )


def list_annotation_proposal_sets(request: HttpRequest,
                                  filters: ModelRunFilterSchema = Query(...)):
    page_size: int = 10  # TODO: use settings.NINJA_PAGINATION_PER_PAGE?
    page = int(request.GET.get('page', 1))

    qs = filters.filter(AnnotationProposalSet.objects.all().order_by(F('uuid')))

    ids = qs[((page - 1) * page_size) : (page * page_size)].values_list(
        'uuid', flat=True
    )
    total_count = qs.count()

    qs = (
        AnnotationProposalSet.objects.filter(uuid__in=ids).values()
        .annotate(
            id=F('uuid'),
            region=F('region_id'),
            title=Concat(
                Value('Proposal '),
                'originator',
                Value(' '),
                'region_id',
                output_field=CharField(),
            ),
            eval=Value(None, output_field=CharField()),
            performer=JSONObject(
                id=0, team_name=F('originator'), short_code=F('originator')
            ),
            parameters=Value({}, output_field=JSONField()),
            created=F('create_datetime'),
            expiration_time=Value(None, output_field=DateTimeField()),
            evaluation=Value(None, output_field=DateTimeField()),
            evaluation_run=Value(None, output_field=DateTimeField()),
            proposal=Value(None, output_field=CharField()),
            adjudicated=JSONObject(
                proposed=0,
                other=0,
            ),
            score=Value(None, output_field=FloatField()),
            numsites=Count('annotationproposalsite'),
            timestamp=ExtractEpoch(Max('annotationproposalsite__end_date')),
            timerange=JSONObject(
                min=ExtractEpoch(Min('annotationproposalsite__start_date')),
                max=ExtractEpoch(Max('annotationproposalsite__end_date')),
            ),
            bbox=Func(
                F('region_id__geometry'),
                4326,
                function='ST_AsGeoJSON',
                output_field=JSONField(),
            ),
        )
    ).order_by(
        F('uuid')
    )

    aggregate_kwargs = {
        'timerange': JSONObject(
            min=ExtractEpoch(Min('annotationproposalsite__start_date')),
            max=ExtractEpoch(Max('annotationproposalsite__end_date')),
        ),
    }

    if filters.region:
        aggregate_kwargs['bbox'] = Max(
            Func(
                F('region_id__geometry'),
                4326,
                function='ST_AsGeoJSON',
                output_field=JSONField(),
            )
        )

    print(qs.query)

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


@router.get('/', response={200: ModelRunPagination.Output})
def list_model_runs(
    request: HttpRequest,
    filters: ModelRunFilterSchema = Query(...),  # noqa: B008
):
    if request.GET.get('proposal'):
        return list_annotation_proposal_sets(request, filters)

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
            evaluationbroadareasearchmetric__min_confidence_score=0.0,
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
    proposal = True if request.GET.get('proposal') else False
    if proposal:
        data = get_object_or_404(get_queryset_proposal(), id=id)
    else:
        data = get_object_or_404(get_queryset(), id=id)

    fetch_counts = SatelliteFetching.objects.filter(
        model_run_uuid=id, status=SatelliteFetching.Status.RUNNING
    ).count()
    data['downloading'] = fetch_counts
    return data


@router.post('/{uuid}/generate-images/', response={202: bool})
def generate_images(
    request: HttpRequest,
    uuid: UUID4,
    params: GenerateImagesSchema = Query(...),  # noqa: B008
):
    proposal = True if request.GET.get('proposal') else False
    scalVal = params.scale
    if params.scale == 'custom':
        scalVal = params.scaleNum
    generate_site_images_for_evaluation_run(
        uuid,
        proposal,
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
    '/{uuid}/cancel-generate-images/',
    response={202: bool, 409: str, 404: str},
)
def cancel_generate_images(request: HttpRequest, uuid: UUID4):
    proposal = True if request.GET.get('proposal') else False

    if proposal:
        get_object_or_404(AnnotationProposalSet, uuid=uuid)
    else:
        get_object_or_404(EvaluationRun, uuid=uuid)

    cancel_generate_images_task.delay(uuid, proposal)

    return 202, True

def get_region(annotation_proposal_set_uuid: UUID4):
    return (
        AnnotationProposalSet.objects
        .filter(pk=annotation_proposal_set_uuid)
        .annotate(
            json=JSONObject(
                region=Subquery(  # prevents including "region" in slow GROUP BY
                    Region.objects.filter(pk=OuterRef('region_id')).values('id')[:1],
                    output_field=JSONField(),
                ),
            ),
        )
    )


def get_proposals_query(annotation_proposal_set_uuid: UUID4):
    proposal_sites = (AnnotationProposalSite.objects
        # .select_related('siteimage', 'satellite_fetching')
        .filter(annotation_proposal_set_uuid=annotation_proposal_set_uuid)
        # .annotate(
        #     siteimage_count=Count('siteimage'),
        #     S2=Count(Case(When(siteimage__source='S2', then=1))),
        #     WV=Count(Case(When(siteimage__source='WV', then=1))),
        #     L8=Count(Case(When(siteimage__source='L8', then=1))),
        #     PL=Count(Case(When(siteimage__source='PL', then=1))),
        #     time=ExtractEpoch('timestamp'),
        #     site_id=F('id'),
        #     downloading=Exists(
        #         SatelliteFetching.objects.filter(
        #             site=OuterRef('pk'),
        #             status=SatelliteFetching.Status.RUNNING,
        #         )
        #     ),
        # )
        .aggregate(
            proposed_sites=JSONBAgg(
                JSONObject(
                    id='uuid',
                    # timestamp='time',
                    number=Cast(Substr('site_id', 9), IntegerField()),
                    bbox=BoundingBox(
                        Func(
                            F('geometry'),
                            4326,
                            function='ST_GeomFromText',
                            output_field=GeometryField(),
                        )
                    ),
                    #             images='siteimage_count',
                    #             S2='S2',
                    #             WV='WV',
                    #             L8='L8',
                    start_date=ExtractEpoch('start_date'),
                    end_date=ExtractEpoch('end_date'),
                    status='proposal_status',
                    #             filename='cache_originator_file',
                    #             downloading='downloading',
                ),
                ordering='site_id',
                default=[],
            ),
        )
    )
    site_ids = [str(s['id']) for s in proposal_sites['proposed_sites']]

    image_queryset = (
        SiteImage.objects.filter(site__in=site_ids)
        .order_by('timestamp')
        .annotate(
            S2=Count(Case(When(source='S2', then=1))),
            WV=Count(Case(When(source='WV', then=1))),
            L8=Count(Case(When(source='L8', then=1))),
            PL=Count(Case(When(source='PL', then=1))),
            downloading=Exists(
                SatelliteFetching.objects.filter(
                    site=OuterRef('site'),
                    status=SatelliteFetching.Status.RUNNING,
                )
            ),
        )
        .aggregate(
            count=Count('pk'),
            results=JSONBAgg(
                JSONObject(
                    timestamp=ExtractEpoch('timestamp'),
                    S2='S2',
                    WV='WV',
                    L8='L8',
                    downloading='downloading',
                ),
                default=[],
            ),
        )
    )
    print(SatelliteFetching)

    for s in proposal_sites['proposed_sites']:
        s['images'] = 1
        s['timestamp'] = None
        s['S2'] = 1
        s['WV'] = 0
        s['L8'] = 0
        s['downloading'] = False

    return proposal_sites


@router.get('/{annotation_proposal_set_uuid}/proposals')
def get_proposals(request: HttpRequest, annotation_proposal_set_uuid: UUID4):
    region = get_region(annotation_proposal_set_uuid).values_list('json', flat=True)
    if not region.exists():
        raise Http404()

    query = get_proposals_query(annotation_proposal_set_uuid)
    model_run = region[0]
    query['region'] = model_run['region']
    return 200, query
