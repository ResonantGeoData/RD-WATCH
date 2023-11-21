import json
import sys
import tempfile
from datetime import datetime

from ninja import Field, FilterSchema, Query, Router, Schema
from pydantic import UUID4

from django.conf import settings
from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.gis.db.models.functions import Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SiteEvaluation, SiteEvaluationTracking, lookups
from rdwatch.schemas import SiteEvaluationRequest
from rdwatch.schemas.common import BoundingBoxSchema, TimeRangeSchema

from .performer import PerformerSchema

router = Router()


class SiteEvaluationSchema(Schema):
    id: int
    site: str
    configuration: dict
    performer: PerformerSchema
    score: float
    timestamp: int | None
    timerange: TimeRangeSchema | None
    bbox: BoundingBoxSchema


class SiteEvaluationListSchema(Schema):
    count: int
    timerange: TimeRangeSchema | None
    status: str | None
    bbox: BoundingBoxSchema
    performers: list[str]
    results: list[SiteEvaluationSchema]
    next: str | None
    previous: str | None


class SiteEvaluationFilterSchema(FilterSchema):
    performer: str | None = Field(q='configuration__performer__slug')
    score: int | None
    timestamp_before: str | None
    timestamp_after: str | None

    @staticmethod
    def _filter_timestamp(date: str, query: str) -> Q:
        parsed_date = datetime.strptime(date, '%Y-%m-%d')
        kwargs = {}
        kwargs[query] = parsed_date
        return Q(**kwargs)

    def filter_timestamp_before(self, value: str | None) -> Q:
        if value is None:
            return Q()
        return self._filter_timestamp(value, 'timestamp__lte')

    def filter_timestamp_after(self, value: str | None) -> Q:
        if value is None:
            return Q()
        return self._filter_timestamp(value, 'timestamp__gte')


@router.get('/', response=SiteEvaluationListSchema)
def list_site_evaluations(
    request: HttpRequest,
    filters: SiteEvaluationFilterSchema = Query(...),  # noqa: B008
):
    queryset: QuerySet[SiteEvaluation] = filters.filter(
        SiteEvaluation.objects.order_by('-timestamp')
    )

    # Overview
    overview = queryset.annotate(
        timerange=JSONObject(
            min=ExtractEpoch('start_time'),
            max=ExtractEpoch('end_date'),
        ),
        status='status',
    ).aggregate(
        count=Count('pk'),
        bbox=BoundingBox(Collect('geom')),
    )

    overview['performers'] = list(
        SiteEvaluation.objects.values_list(
            'configuration__performer__slug', flat=True
        ).distinct()
    )

    # Pagination
    assert (
        settings.NINJA_PAGINATION_PAGE_SIZE
    ), 'NINJA_PAGINATION_PAGE_SIZE must be set.'
    limit = (
        int(request.GET.get('limit', settings.NINJA_PAGINATION_PAGE_SIZE))
        or sys.maxsize
    )
    paginator = Paginator(queryset, limit)
    page = paginator.page(request.GET.get('page', 1))

    if page.has_next():
        next_page_query_params = request.GET.copy()
        next_page_query_params['page'] = str(page.next_page_number())
        overview['next'] = f'{request.path}?{next_page_query_params.urlencode()}'
    else:
        overview['next'] = None

    if page.has_previous():
        prev_page_query_params = request.GET.copy()
        prev_page_query_params['page'] = str(page.previous_page_number())
        overview['previous'] = f'{request.path}?{prev_page_query_params.urlencode()}'
    else:
        overview['previous'] = None

    # Results
    results = page.object_list.annotate(  # type: ignore
        timemin='start_date',
        timemax='end_date',
    ).aggregate(
        results=JSONBAgg(
            JSONObject(
                id='pk',
                site=JSONObject(
                    region='region__name',
                    number='number',
                ),
                configuration='configuration__parameters',
                performer=JSONObject(
                    id='configuration__performer__id',
                    team_name='configuration__performer__description',
                    short_code='configuration__performer__slug',
                ),
                score='score',
                bbox=BoundingBox('geom'),
                timestamp=ExtractEpoch('timestamp'),
                timerange=JSONObject(
                    min=ExtractEpoch('timemin'),
                    max=ExtractEpoch('timemax'),
                ),
            )
        ),
    )

    return overview | results


class SiteDetailResponse(Schema):
    region_name: str
    configuration_id: str | int  # some values still ints in my case
    number: str
    version: str
    title: str
    performer: str | None
    timemin: int | None
    timemax: int | None

    @staticmethod
    def resolve_region_name(obj: SiteEvaluation) -> str:
        return obj.region.name

    @staticmethod
    def resolve_title(obj: SiteEvaluation) -> str:
        return obj.configuration.title

    @staticmethod
    def resolve_performer(obj: SiteEvaluation) -> str:
        return obj.configuration.performer.slug

    @staticmethod
    def resolve_timemin(obj: SiteEvaluation) -> int | None:
        if obj.start_date:
            return obj.start_date.timestamp()
        return None

    @staticmethod
    def resolve_timemax(obj: SiteEvaluation) -> int | None:
        if obj.end_date:
            return obj.end_date.timestamp()
        return None


@router.get('/{id}/', response=SiteDetailResponse)
def get_site_evaluation(request: HttpRequest, id: UUID4):
    return get_object_or_404(
        SiteEvaluation.objects.select_related(
            'configuration', 'configuration__performer', 'region'
        ),
        id=id,
    )


@router.patch('/{id}/')
def patch_site_evaluation(request: HttpRequest, id: UUID4, data: SiteEvaluationRequest):
    with transaction.atomic():
        site_evaluation = get_object_or_404(
            SiteEvaluation.objects.select_for_update(), pk=id
        )
        # create a copy of it in the history log
        SiteEvaluationTracking.objects.create(
            score=site_evaluation.score,
            label=site_evaluation.label,
            end_date=site_evaluation.end_date,
            start_date=site_evaluation.start_date,
            notes=site_evaluation.notes,
            edited=datetime.now(),
            evaluation=site_evaluation,
        )

        if data.label:
            site_evaluation.label = lookups.ObservationLabel.objects.get(
                slug=data.label
            )

        # Use `exclude_unset` here because an explicitly `null` start/end date
        # means something different than a missing start/end date.
        data_dict = data.dict(exclude_unset=True)

        FIELDS = ('start_date', 'end_date', 'notes', 'status')
        for field in filter(lambda f: f in data_dict, FIELDS):
            setattr(site_evaluation, field, data_dict[field])

        site_evaluation.save()

    return 200


def get_site_model_feature_JSON(id: UUID4, obsevations=False):
    query = (
        SiteEvaluation.objects.filter(pk=id)
        .values()
        .annotate(
            json=JSONObject(
                site=JSONObject(
                    region='region__name',
                    number='number',
                ),
                configuration='configuration__parameters',
                version='version',
                performer=JSONObject(
                    id='configuration__performer__id',
                    team_name='configuration__performer__description',
                    short_code='configuration__performer__slug',
                ),
                cache_originator_file='cache_originator_file',
                cache_timestamp='cache_timestamp',
                cache_commit_hash='cache_commit_hash',
                notes='notes',
                score='score',
                status='label__slug',
                geom=Transform('geom', srid=4326),
                start_date=('start_date'),
                end_date=('end_date'),
            )
        )
    )
    if query.exists():
        data = query[0]['json']

        region_name = data['site']['region']
        site_id = f'{region_name}_{str(data["site"]["number"]).zfill(4)}'
        version = data['version']
        output = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': {
                        'type': 'site',
                        'region_id': region_name,
                        'site_id': site_id,
                        'version': version,
                        'status': data['status'],
                        'score': data['score'],
                        'start_date': None
                        if data['start_date'] is None
                        else datetime.fromisoformat(data['start_date']).strftime(
                            '%Y-%m-%d'
                        ),
                        'end_date': None
                        if data['end_date'] is None
                        else datetime.fromisoformat(data['end_date']).strftime(
                            '%Y-%m-%d'
                        ),
                        'model_content': 'annotation',
                        'originator': data['performer']['short_code'],
                    },
                    'geometry': data['geom'],
                }
            ],
        }
        filename = None
        if data['cache_originator_file']:
            filename = data['cache_originator_file']
            output['features'][0]['properties']['cache'] = {
                'cache_originator_file': data['cache_originator_file'],
                'cache_timestamp': data['cache_timestamp'],
                'cache_commit_hash': data['cache_commit_hash'],
                'cache_notes': data['notes'],
            }
        return output, site_id, filename
    return None, None


@router.get('/{id}/download')
def download_annotations(request: HttpRequest, id: UUID4):
    output, site_id, filename = get_site_model_feature_JSON(id)
    if output is not None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            json_data = json.dumps(output).encode('utf-8')
            temp_file.write(json_data)

        # Return the temporary file for download
        with open(temp_file.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename={site_id}.json'

            return response
    # TODO: Some Better Error response
    return 500, 'Unable to export data'
