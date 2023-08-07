import json
import os
import tempfile
import zipfile
from datetime import datetime, timedelta

import iso3166
from celery.result import AsyncResult
from ninja import Field, FilterSchema, Query, Schema
from ninja.errors import ValidationError
from ninja.pagination import RouterPaginated
from ninja.schema import validator
from pydantic import constr  # type: ignore

from django.contrib.postgres.aggregates import JSONBAgg
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
    Subquery,
    When,
)
from django.db.models.functions import Coalesce, JSONObject
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.db.functions import (
    AggregateArraySubquery,
    BoundingBox,
    BoundingBoxGeoJSON,
    ExtractEpoch,
)
from rdwatch.models import (
    HyperParameters,
    Region,
    SatelliteFetching,
    SiteEvaluation,
    lookups,
)
from rdwatch.schemas import RegionModel, SiteModel
from rdwatch.schemas.common import TimeRangeSchema
from rdwatch.views.performer import PerformerSchema
from rdwatch.views.region import RegionSchema
from rdwatch.views.site_evaluation import get_site_model_feature_JSON
from rdwatch.views.site_observation import get_site_observation_images

router = RouterPaginated()


class ModelRunFilterSchema(FilterSchema):
    performer: str | None = Field(q='performer_slug')
    region: str | None
    proposal: str | None = Field(q='proposal', ignore_none=False)

    def filter_region(self, value: str | None) -> Q:
        if value is None:
            return Q()
        countrystr, numstr = value.split('_')
        country = iso3166.countries_by_alpha2[countrystr].numeric
        classification_slug = numstr[0]
        number = None if numstr[1:] == 'xxx' else int(numstr[1:])
        return (
            Q(region_country=country)
            & Q(region_class_slug=classification_slug)
            & Q(region_number=number)
        )


class HyperParametersWriteSchema(Schema):
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


class HyperParametersAdjudicated(Schema):
    proposed: int
    other: int


class HyperParametersDetailSchema(Schema):
    id: int
    title: str
    region: RegionSchema | None = None
    performer: PerformerSchema
    parameters: dict
    numsites: int
    downloading: int | None = None
    score: float | None = None
    timestamp: int | None = None
    timerange: TimeRangeSchema | None = None
    bbox: dict | None
    created: datetime
    expiration_time: str | None = None
    evaluation: int | None = None
    evaluation_run: int | None = None
    proposal: str = None
    adjudicated: HyperParametersAdjudicated | None = None


class EvaluationListSchema(Schema):
    id: int
    siteNumber: int
    region: RegionSchema | None


class HyperParametersListSchema(Schema):
    count: int
    timerange: TimeRangeSchema | None = None
    bbox: dict | None = None
    results: list[HyperParametersDetailSchema]


def get_queryset():
    # Subquery to count unique SiteEvaluations
    # with proposal='PROPOSAL' for each HyperParameters
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
    # not equal to 'PROPOSAL' for each HyperParameters
    other_count_subquery = (
        SiteEvaluation.objects.filter(configuration=OuterRef('pk'))
        .exclude(status='PROPOSAL')
        .values('configuration')
        .annotate(count=Count('pk'))
        .values('count')
    )

    return (
        HyperParameters.objects.select_related(
            'evaluations', 'performer', 'satellitefetching'
        )
        # Get minimum score and performer so that we can tell which runs
        # are ground truth
        .alias(min_score=Min('evaluations__score'), performer_slug=F('performer__slug'))
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
            observation_count=Count('evaluations__observations'),
            evaluation_configuration=F('evaluations__configuration'),
            proposal_val=F('proposal'),
        )
        .annotate(
            json=JSONObject(
                id='pk',
                title='title',
                created='created',
                expiration_time='expiration_time',
                performer=Subquery(  # prevents including "performer" in slow GROUP BY
                    lookups.Performer.objects.filter(
                        pk=OuterRef('performer_id')
                    ).values(
                        json=JSONObject(
                            id='id',
                            team_name='description',
                            short_code='slug',
                        )
                    ),
                    output_field=JSONField(),
                ),
                region=Subquery(  # prevents including "region" in slow GROUP BY
                    Region.objects.filter(pk=OuterRef('region_id')).values(
                        json=JSONObject(
                            id='id',
                            country='country',
                            classification=JSONObject(slug='classification__slug'),
                            number='number',
                        )
                    ),
                    output_field=JSONField(),
                ),
                downloading=Coalesce(
                    Subquery(
                        SatelliteFetching.objects.filter(
                            siteeval__configuration_id=OuterRef(
                                'evaluation_configuration'
                            ),
                            status=SatelliteFetching.Status.RUNNING,
                        )
                        .annotate(count=Func(F('id'), function='Count'))
                        .values('count')
                    ),
                    0,  # Default value when evaluations are None
                ),
                parameters='parameters',
                numsites=Count('evaluations__pk', distinct=True),
                score=Avg('evaluations__score'),
                evaluation='evaluation',
                evaluation_run='evaluation_run',
                timestamp=ExtractEpoch(Max('evaluations__timestamp')),
                timerange=JSONObject(
                    min=ExtractEpoch(Min('evaluations__start_date')),
                    max=ExtractEpoch(Max('evaluations__end_date')),
                ),
                bbox=Case(
                    # If there are no site observations associated with this
                    # site evaluation, return the bbox of the site polygon.
                    # Otherwise, return the bounding box of all observation
                    # polygons.
                    When(
                        observation_count=0,
                        then=BoundingBoxGeoJSON('evaluations__geom'),
                    ),
                    default=BoundingBoxGeoJSON('evaluations__observations__geom'),
                ),
                proposal='proposal_val',
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
    )


@router.post('/', response={200: HyperParametersDetailSchema}, exclude_none=True)
def create_model_run(
    request: HttpRequest,
    hyper_parameters_data: HyperParametersWriteSchema,
):
    hyper_parameters = HyperParameters.objects.create(
        title=hyper_parameters_data.title,
        performer=hyper_parameters_data.performer,
        parameters=hyper_parameters_data.parameters,
        expiration_time=hyper_parameters_data.expiration_time,
        evaluation=hyper_parameters_data.evaluation,
        evaluation_run=hyper_parameters_data.evaluation_run,
        proposal=hyper_parameters_data.proposal,
    )
    return 200, {
        'id': hyper_parameters.pk,
        'title': hyper_parameters.title,
        'performer': {
            'id': hyper_parameters.performer.pk,
            'team_name': hyper_parameters.performer.description,
            'short_code': hyper_parameters.performer.slug,
        },
        'parameters': hyper_parameters.parameters,
        'numsites': 0,
        'created': hyper_parameters.created,
        'expiration_time': str(hyper_parameters.expiration_time),
    }


@router.get('/', response={200: HyperParametersListSchema})
def list_model_runs(
    request: HttpRequest,
    filters: ModelRunFilterSchema = Query(...),  # noqa: B008
    limit: int = 25,
    page: int = 1,
):
    queryset = get_queryset()
    queryset = filters.filter(
        queryset.alias(
            min_score=Min('evaluations__score'),
            performer_slug=F('performer__slug'),
            region_country=F('evaluations__region__country'),
            region_class_slug=F('evaluations__region__classification__slug'),
            region_number=F('evaluations__region__number'),
        )
    )

    if page < 1 or (not limit and page != 1):
        raise ValidationError(f"Invalid page '{page}'")

    # Calculate total number of model runs prior to paginating queryset
    total_model_run_count = queryset.count()

    subquery = queryset[(page - 1) * limit : page * limit] if limit else queryset
    aggregate = queryset.defer('json').aggregate(
        timerange=JSONObject(
            min=ExtractEpoch(Min('evaluations__start_date')),
            max=ExtractEpoch(Max('evaluations__end_date')),
        ),
        results=AggregateArraySubquery(subquery.values('json')),
    )

    aggregate['count'] = total_model_run_count

    # TODO: use a resolver instead.
    # Temporary until https://github.com/vitalik/django-ninja/issues/610 is fixed
    for result in aggregate['results']:
        if result['region']:
            result['region'] = {
                'name': RegionSchema.resolve_name(result['region']),
                'id': result['region']['id'],
            }

    # Only bother calculating the entire bounding box of this model run
    # list if the user has specified a region. We don't want to overload
    # PostGIS by making it calculate a bounding box for every polygon in
    # the database.
    if filters.region is not None:
        aggregate |= queryset.defer('json').aggregate(
            # Use the region polygon for the bbox if it exists.
            # Otherwise, fall back on the site polygon.
            bbox=Coalesce(
                BoundingBoxGeoJSON('evaluations__region__geom'),
                BoundingBoxGeoJSON('evaluations__geom'),
            )
        )

    if aggregate['count'] > 0 and not aggregate['results']:
        raise ValidationError({'page': f"Invalid page '{page}'"})

    return 200, aggregate


@router.get('/{id}/', response={200: HyperParametersDetailSchema})
def get_model_run(request: HttpRequest, id: int):
    values = get_queryset().filter(id=id).values_list('json', flat=True)

    if not values.exists():
        raise Http404()

    model_run = values[0]

    # TODO: use a resolver instead.
    # Temporary until https://github.com/vitalik/django-ninja/issues/610 is fixed
    if model_run['region']:
        model_run['region'] = {
            'name': RegionSchema.resolve_name(model_run['region']),
            'id': model_run['region']['id'],
        }

    return 200, model_run


@router.post(
    '/{hyper_parameters_id}/site-model/',
    response={201: int},
)
def post_site_model(
    request: HttpRequest,
    hyper_parameters_id: int,
    site_model: SiteModel,
):
    hyper_parameters = get_object_or_404(HyperParameters, pk=hyper_parameters_id)
    site_evaluation = SiteEvaluation.bulk_create_from_site_model(
        site_model, hyper_parameters
    )
    return 201, site_evaluation.id


@router.post(
    '/{hyper_parameters_id}/region-model/',
    response={201: list[int]},
)
def post_region_model(
    request: HttpRequest,
    hyper_parameters_id: int,
    region_model: RegionModel,
):
    hyper_parameters = get_object_or_404(HyperParameters, pk=hyper_parameters_id)
    site_evaluations = SiteEvaluation.bulk_create_from_from_region_model(
        region_model, hyper_parameters
    )
    return 201, [eval.id for eval in site_evaluations]


@router.post('/{hyper_parameters_id}/generate-images/', response={202: bool})
def generate_images(request: HttpRequest, hyper_parameters_id: int):
    siteEvaluations = SiteEvaluation.objects.filter(configuration=hyper_parameters_id)

    for eval in siteEvaluations:
        get_site_observation_images(request, eval.pk)

    return 202, True


@router.put(
    '/{hyper_parameters_id}/cancel-generate-images/',
    response={202: bool, 409: str, 404: str},
)
def cancel_generate_images(request: HttpRequest, hyper_parameters_id: int):
    siteEvaluations = SiteEvaluation.objects.filter(configuration=hyper_parameters_id)

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


def get_region(hyper_parameters_id: int):
    return (
        HyperParameters.objects.select_related('evaluations')
        .filter(pk=hyper_parameters_id)
        .alias(
            region_id=F('evaluations__region_id'),
        )
        .annotate(
            json=JSONObject(
                region=Subquery(  # prevents including "region" in slow GROUP BY
                    Region.objects.filter(pk=OuterRef('region_id')).values(
                        json=JSONObject(
                            id='id',
                            country='country',
                            classification=JSONObject(slug='classification__slug'),
                            number='number',
                        )
                    ),
                    output_field=JSONField(),
                ),
            ),
        )
    )


def get_evaluations_query(hyper_parameters_id: int):
    return (
        SiteEvaluation.objects.select_related('siteimage')
        .filter(configuration=hyper_parameters_id)
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
                ),
                ordering='number',
            ),
        )
    )


@router.get('/{hyper_parameters_id}/evaluations')
def get_modelrun_evaluations(request: HttpRequest, hyper_parameters_id: int):
    region = get_region(hyper_parameters_id).values_list('json', flat=True)
    if not region.exists():
        raise Http404()

    query = get_evaluations_query(hyper_parameters_id)
    model_run = region[0]
    # TODO: use a resolver instead.
    # Temporary until https://github.com/vitalik/django-ninja/issues/610 is fixed
    if model_run['region']:
        model_run['region'] = {
            'name': RegionSchema.resolve_name(model_run['region']),
            'id': model_run['region']['id'],
        }
    query['region'] = model_run['region']
    return 200, query


@router.get('/{id}/download')
def download_annotations(request: HttpRequest, id: int):
    # Needs to go through the siteEvaluations and download one for each file
    site_evals = SiteEvaluation.objects.filter(configuration_id=id)
    model_run_name = HyperParameters.objects.get(pk=id).title
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_file_path = os.path.join(temp_dir, 'annotations.zip')
        file_list = []
        for item in site_evals:
            data, site_id = get_site_model_feature_JSON(item.pk)
            file_name = os.path.join(temp_dir, f'{site_id}.json')
            with open(file_name, 'w') as file:
                json.dump(data, file)
            file_list.append({'filename': file_name, 'siteId': site_id})
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for item in file_list:
                zipf.write(item['filename'], f"{item['siteId']}.json")

        with open(zip_file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/zip')
            response[
                'Content-Disposition'
            ] = f'attachment; filename="{model_run_name}.zip"'
            return response
