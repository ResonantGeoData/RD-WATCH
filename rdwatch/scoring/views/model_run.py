import logging
from typing import Literal, TypeAlias

from ninja import FilterSchema, Query
from ninja.pagination import RouterPaginated
from pydantic import UUID4

from django.contrib.gis.db.models import GeometryField
from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    DateTimeField,
    Exists,
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
    Subquery,
    Value,
    When,
)
from django.db.models.functions import (
    Cast,
    Coalesce,
    Concat,
    JSONObject,
    NullIf,
    Substr,
)
from django.http import Http404, HttpRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from rdwatch.core.db.functions import BoundingBox, ExtractEpoch
from rdwatch.core.views.model_run import ModelRunDetailSchema, ModelRunPagination
from rdwatch.scoring.models import (
    AnnotationProposalSet,
    AnnotationProposalSite,
    EvaluationBroadAreaSearchDetection,
    EvaluationBroadAreaSearchProposal,
    EvaluationRun,
    Region,
    SatelliteFetching,
    Site,
    SiteImage,
)
from rdwatch.scoring.tasks import (
    cancel_generate_images_task,
    generate_site_images_for_evaluation_run,
)
from rdwatch.scoring.views.site_observation import GenerateImagesSchema

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
        for performer_code in value:
            performer_q |= Q(performer=performer_code)
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


def get_queryset(id: UUID4):
    return (
        EvaluationRun.objects.filter(
            Q(uuid=id),
            Q(evaluationbroadareasearchmetric__activity_type='overall'),
            Q(evaluationbroadareasearchmetric__tau=0.2),
            Q(evaluationbroadareasearchmetric__rho=0.5),
            Q(evaluationbroadareasearchmetric__min_confidence_score=0.0),
            Q(evaluationbroadareasearchmetric__min_spatial_distance_threshold=None)
            | Q(evaluationbroadareasearchmetric__min_spatial_distance_threshold=100.0),
            Q(evaluationbroadareasearchmetric__central_spatial_distance_threshold=None)
            | Q(
                evaluationbroadareasearchmetric__central_spatial_distance_threshold=500.0  # noqa: E501
            ),
            Q(evaluationbroadareasearchmetric__max_spatial_distance_threshold=None),
            Q(evaluationbroadareasearchmetric__min_temporal_distance_threshold=None)
            | Q(evaluationbroadareasearchmetric__min_temporal_distance_threshold=730.0),
            Q(
                evaluationbroadareasearchmetric__central_temporal_distance_threshold=None  # noqa: E501
            ),
            Q(evaluationbroadareasearchmetric__max_temporal_distance_threshold=None),
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
            region_name=F('region'),
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
            timestamp=Coalesce(
                ExtractEpoch(Max('site__end_date')),
                ExtractEpoch(Max('site__point_date')),
            ),
            timerange=JSONObject(
                min=Coalesce(
                    ExtractEpoch(Min('site__start_date')),
                    ExtractEpoch(Min('site__point_date')),
                ),
                max=Coalesce(
                    ExtractEpoch(Max('site__end_date')),
                    ExtractEpoch(Max('site__point_date')),
                ),
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


def get_queryset_proposal(id: UUID4):
    proposed_count_subquery = (
        AnnotationProposalSite.objects.filter(
            annotation_proposal_set_uuid=OuterRef('pk')
        )
        .filter(proposal_status='PROPOSAL')
        .values('annotation_proposal_set_uuid')
        .annotate(count=Count('pk'))
        .values('count')
    )
    other_count_subquery = (
        AnnotationProposalSite.objects.filter(
            annotation_proposal_set_uuid=OuterRef('pk')
        )
        .exclude(proposal_status='PROPOSAL')
        .values('annotation_proposal_set_uuid')
        .annotate(count=Count('pk'))
        .values('count')
    )

    return (
        AnnotationProposalSet.objects.filter(annotation_proposal_set_uuid=id)
        .values()
        .annotate(
            id=F('uuid'),
            region_name=F('region_id'),
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
            proposal=Value(True),
            adjudicated=JSONObject(
                proposed=Coalesce(Subquery(proposed_count_subquery), 0),
                other=Coalesce(Subquery(other_count_subquery), 0),
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
    ).order_by(F('uuid'))


def list_annotation_proposal_sets(
    request: HttpRequest,
    filters: ModelRunFilterSchema,  # noqa: B008
):
    page_size: int = 10  # TODO: use settings.NINJA_PAGINATION_PER_PAGE?
    page = int(request.GET.get('page', 1))

    qs = filters.filter(AnnotationProposalSet.objects.all().order_by('uuid'))

    ids = qs[((page - 1) * page_size) : (page * page_size)].values_list(
        'uuid', flat=True
    )
    total_count = qs.count()

    proposed_count_subquery = (
        AnnotationProposalSite.objects.filter(
            annotation_proposal_set_uuid=OuterRef('pk')
        )
        .filter(proposal_status='PROPOSAL')
        .values('annotation_proposal_set_uuid')
        .annotate(count=Count('pk'))
        .values('count')
    )
    other_count_subquery = (
        AnnotationProposalSite.objects.filter(
            annotation_proposal_set_uuid=OuterRef('pk')
        )
        .exclude(proposal_status='PROPOSAL')
        .values('annotation_proposal_set_uuid')
        .annotate(count=Count('pk'))
        .values('count')
    )

    qs = (
        AnnotationProposalSet.objects.filter(uuid__in=ids)
        .values()
        .annotate(
            id=F('uuid'),
            region_name=F('region_id'),
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
            proposal=Value(True, output_field=CharField()),
            adjudicated=JSONObject(
                proposed=Coalesce(Subquery(proposed_count_subquery), 0),
                other=Coalesce(Subquery(other_count_subquery), 0),
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
    ).order_by(F('uuid'))

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
    proposal: Literal['PROPOSAL', 'APPROVED', None] = None,
    page: int = 1,
    filters: ModelRunFilterSchema = Query(...),  # noqa: B008
):
    if proposal:
        return list_annotation_proposal_sets(request, filters)

    page_size: int = 10  # TODO: use settings.NINJA_PAGINATION_PER_PAGE?

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
            Q(uuid__in=ids),
            Q(evaluationbroadareasearchmetric__activity_type='overall'),
            Q(evaluationbroadareasearchmetric__tau=0.2),
            Q(evaluationbroadareasearchmetric__rho=0.5),
            Q(evaluationbroadareasearchmetric__min_confidence_score=0.0),
            Q(evaluationbroadareasearchmetric__min_spatial_distance_threshold=None)
            | Q(evaluationbroadareasearchmetric__min_spatial_distance_threshold=100.0),
            Q(evaluationbroadareasearchmetric__central_spatial_distance_threshold=None)
            | Q(
                evaluationbroadareasearchmetric__central_spatial_distance_threshold=500.0  # noqa: E501
            ),
            Q(evaluationbroadareasearchmetric__max_spatial_distance_threshold=None),
            Q(evaluationbroadareasearchmetric__min_temporal_distance_threshold=None)
            | Q(evaluationbroadareasearchmetric__min_temporal_distance_threshold=730.0),
            Q(
                evaluationbroadareasearchmetric__central_temporal_distance_threshold=None  # noqa: E501
            ),
            Q(evaluationbroadareasearchmetric__max_temporal_distance_threshold=None),
        )
        .values()
        .annotate(
            id=F('uuid'),
            region_name=F('region'),
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
            timestamp=Coalesce(
                ExtractEpoch(Max('site__end_date')),
                ExtractEpoch(Max('site__point_date')),
            ),
            timerange=JSONObject(
                min=Coalesce(
                    ExtractEpoch(Min('site__start_date')),
                    ExtractEpoch(Min('site__point_date')),
                ),
                max=Coalesce(
                    ExtractEpoch(Max('site__end_date')),
                    ExtractEpoch(Max('site__point_date')),
                ),
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
            min=Coalesce(
                ExtractEpoch(Min('site__start_date')),
                ExtractEpoch(Min('site__point_date')),
            ),
            max=Coalesce(
                ExtractEpoch(Max('site__end_date')),
                ExtractEpoch(Max('site__point_date')),
            ),
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
    if EvaluationRun.objects.filter(pk=id).exists():
        data = get_queryset(id=id).first()
    elif AnnotationProposalSet.objects.filter(pk=id).exists():
        data = get_object_or_404(get_queryset_proposal(), id=id)
    else:
        return HttpResponseNotFound(
            f'Neither an EvaluationRun or AnnotationProposalSet exists for uuid: {id}'
        )

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
    scalVal = params.scale
    if params.scale == 'custom':
        scalVal = params.scaleNum
    generate_site_images_for_evaluation_run(
        uuid,
        params.constellation,
        params.force,
        params.dayRange,
        params.noData,
        params.overrideDates,
        scalVal,
        params.bboxScale,
        params.pointArea,
        params.worldviewSource

    )
    return 202, True


@router.put(
    '/{uuid}/cancel-generate-images/',
    response={202: bool, 409: str, 404: str},
)
def cancel_generate_images(request: HttpRequest, uuid: UUID4):
    try:
        EvaluationRun.objects.get(uuid=uuid)
    except EvaluationRun.DoesNotExist:
        get_object_or_404(AnnotationProposalSet, uuid=uuid)

    cancel_generate_images_task.delay(uuid)

    return 202, True


def get_region(annotation_proposal_set_uuid: UUID4):
    return AnnotationProposalSet.objects.filter(
        pk=annotation_proposal_set_uuid
    ).annotate(
        json=JSONObject(
            region=Subquery(  # prevents including "region" in slow GROUP BY
                Region.objects.filter(pk=OuterRef('region_id')).values('id')[:1],
                output_field=JSONField(),
            ),
        ),
    )


def get_proposals_query(annotation_proposal_set_uuid: UUID4):
    proposal_sites = (
        AnnotationProposalSite.objects
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
            sites=JSONBAgg(
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
    site_ids = [str(s['id']) for s in proposal_sites['sites']]
    image_queryset = (
        SiteImage.objects.filter(site__in=site_ids)
        .values('site')
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
    )

    image_info = {i['site']: i for i in image_queryset}
    for s in proposal_sites['sites']:
        if s['id'] in image_info.keys():
            site_image_info = image_info[s['id']]
        else:
            site_image_info = {'S2': 0, 'WV': 0, 'L8': 0, 'PL': 0, 'downloading': False}

        s['images'] = (
            site_image_info['S2']
            + site_image_info['WV']
            + site_image_info['L8']
            + site_image_info['PL']
        )
        s['S2'] = site_image_info['S2']
        s['WV'] = site_image_info['WV']
        s['L8'] = site_image_info['L8']
        s['PL'] = site_image_info['PL']
        s['downloading'] = site_image_info['downloading']
    return proposal_sites


def get_sites_query(model_run_id: UUID4):
    performer = EvaluationRun.objects.get(pk=model_run_id).performer
    site_list = Site.objects.filter(evaluation_run_uuid=model_run_id).aggregate(
        sites=JSONBAgg(
            JSONObject(
                id='pk',
                number=Substr(F('site_id'), 9, 4),  # pos is 1 indexed,
                bbox=BoundingBox(
                    Func(
                        F('union_geometry'),
                        4326,
                        function='ST_GeomFromText',
                        output_field=GeometryField(),
                    )
                ),
                groundtruth=Case(
                    When(
                        ~Q(originator=performer)
                        & (Q(originator='te') | Q(originator='iMERIT')),
                        True,
                    ),
                    default=False,
                ),
                start_date=Coalesce(
                    ExtractEpoch('start_date'), ExtractEpoch('point_date')
                ),
                end_date=Coalesce(ExtractEpoch('end_date'), ExtractEpoch('point_date')),
                originator=F('originator'),
                color_code=Case(
                    When(
                        Q(originator='te') | Q(originator='iMERIT'),
                        then=Subquery(
                            EvaluationBroadAreaSearchDetection.objects.filter(
                                Q(evaluation_run_uuid=model_run_id)
                                & Q(activity_type='overall')
                                & Q(rho=0.5)
                                & Q(tau=0.2)
                                & Q(min_confidence_score=0.0)
                                & Q(site_truth=OuterRef('site_id'))
                                & Q(
                                    Q(min_spatial_distance_threshold__isnull=True)
                                    | Q(min_spatial_distance_threshold=100.0)
                                )
                                & Q(
                                    Q(central_spatial_distance_threshold__isnull=True)
                                    | Q(central_spatial_distance_threshold=500.0)
                                )
                                & Q(max_spatial_distance_threshold__isnull=True)
                                & Q(
                                    Q(min_temporal_distance_threshold__isnull=True)
                                    | Q(min_temporal_distance_threshold=730.0)
                                )
                                & Q(central_temporal_distance_threshold__isnull=True)
                                & Q(max_temporal_distance_threshold__isnull=True)
                            ).values('color_code')
                        ),
                    ),
                    When(
                        ~Q(originator='te') & ~Q(originator='iMERIT'),
                        then=Subquery(
                            EvaluationBroadAreaSearchProposal.objects.filter(
                                Q(evaluation_run_uuid=model_run_id)
                                & Q(activity_type='overall')
                                & Q(rho=0.5)
                                & Q(tau=0.2)
                                & Q(min_confidence_score=0.0)
                                & Q(site_proposal=OuterRef('site_id'))
                                & Q(
                                    Q(min_spatial_distance_threshold__isnull=True)
                                    | Q(min_spatial_distance_threshold=100.0)
                                )
                                & Q(
                                    Q(central_spatial_distance_threshold__isnull=True)
                                    | Q(central_spatial_distance_threshold=500.0)
                                )
                                & Q(max_spatial_distance_threshold__isnull=True)
                                & Q(
                                    Q(min_temporal_distance_threshold__isnull=True)
                                    | Q(min_temporal_distance_threshold=730.0)
                                )
                                & Q(central_temporal_distance_threshold__isnull=True)
                                & Q(max_temporal_distance_threshold__isnull=True)
                            ).values('color_code')
                        ),
                    ),
                    default=Value(None),  # Set an appropriate default value here
                ),
            ),
            ordering='site_id',
            default=[],
        ),
    )
    site_ids = [str(s['id']) for s in site_list['sites']]

    image_queryset = (
        SiteImage.objects.filter(site__in=site_ids)
        .values('site')
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
    )

    image_info = {i['site']: i for i in image_queryset}

    for s in site_list['sites']:
        if s['id'] in image_info.keys():
            site_image_info = image_info[s['id']]
        else:
            site_image_info = {'S2': 0, 'WV': 0, 'L8': 0, 'PL': 0, 'downloading': False}

        s['images'] = (
            site_image_info['S2']
            + site_image_info['WV']
            + site_image_info['L8']
            + site_image_info['PL']
        )
        s['S2'] = site_image_info['S2']
        s['WV'] = site_image_info['WV']
        s['L8'] = site_image_info['L8']
        s['PL'] = site_image_info['PL']
        s['downloading'] = site_image_info['downloading']
    return site_list


def get_model_run_details(model_run_id: UUID4):
    return EvaluationRun.objects.filter(
        pk=model_run_id,
    ).annotate(
        json=JSONObject(
            region=F('region'),
            performer=JSONObject(
                id=0, team_name=F('performer'), short_code=F('performer')
            ),
            version=Coalesce('site__version', Value(None)),
            proposal=False,
            title=ExpressionWrapper(
                Concat(
                    Value('Eval '),
                    F('evaluation_number'),
                    Value(' '),
                    F('evaluation_run_number'),
                    Value(' '),
                    F('performer'),
                ),
                output_field=CharField(),
            ),
        ),
    )


def get_annotation_proposal_set_details(model_run_id: UUID4):
    return AnnotationProposalSet.objects.filter(
        uuid=model_run_id,
    ).annotate(
        json=JSONObject(
            region=F('region_id'),
            performer=JSONObject(
                id=0, team_name=F('originator'), short_code=F('originator')
            ),
            version=Value(None),
            proposal=True,
            title=ExpressionWrapper(
                Concat(
                    Value('Proposals '),
                    F('region_id'),
                    Value(' '),
                    F('originator'),
                ),
                output_field=CharField(),
            ),
        ),
    )


@router.get('/{annotation_proposal_set_uuid}/proposals/')
def get_proposals(request: HttpRequest, annotation_proposal_set_uuid: UUID4):
    data = get_annotation_proposal_set_details(
        annotation_proposal_set_uuid
    ).values_list('json', flat=True)
    if not data.exists():
        raise Http404()

    details = data.first()
    query = get_proposals_query(annotation_proposal_set_uuid)
    query['region'] = details['region']
    query['modelRunDetails'] = details
    return 200, query


@router.get('/{model_run_id}/sites/')
def get_sites(request: HttpRequest, model_run_id: UUID4):
    data = get_model_run_details(model_run_id).values_list('json', flat=True)
    if not data.exists():
        raise Http404()

    query = get_sites_query(model_run_id)
    model_run = data[0]
    # TODO: Remove the region in the client side to focus on modelRunDetails
    query['region'] = model_run['region']
    query['modelRunDetails'] = model_run
    return 200, query
