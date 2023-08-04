import sys
from datetime import datetime
from django.http import HttpResponse
from django.contrib.gis.db.models.functions import AsGeoJSON, Envelope, Transform

import iso3166
from ninja import Field, FilterSchema, Query, Router, Schema

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.paginator import Paginator
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
    QuerySet,
    When,
)
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from rest_framework.settings import api_settings
import iso3166

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SiteEvaluation, SiteEvaluationTracking, lookups, Region
from rdwatch.schemas import SiteEvaluationRequest
from rdwatch.schemas.common import BoundingBoxSchema, TimeRangeSchema

from rdwatch.utils.tools import getRegion
from .performer import PerformerSchema
import json
import tempfile
router = Router()


class SiteEvaluationSchema(Schema):
    id: int
    site: dict
    configuration: dict
    performer: PerformerSchema
    score: float
    timestamp: int | None
    timerange: TimeRangeSchema | None
    bbox: BoundingBoxSchema

    @staticmethod
    def resolve_site(obj: dict) -> str:
        country_numeric = str(obj['region']['country']).zfill(3)
        country_code = iso3166.countries_by_numeric[country_numeric].alpha2
        region_class = obj['region']['classification']
        region_number = (
            'xxx'
            if obj['region']['number'] is None
            else str(obj['region']['number']).zfill(3)
        )
        site_number = str(obj['number']).zfill(3)
        return f'{country_code}_{region_class}{region_number}_{site_number}'


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
    assert api_settings.PAGE_SIZE, 'PAGE_SIZE must be set.'
    limit = int(request.GET.get('limit', api_settings.PAGE_SIZE)) or sys.maxsize
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
                    region=JSONObject(
                        country='region__country',
                        classification='region__classification__slug',
                        number='region__number',
                    ),
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


@router.patch('/{id}/')
def patch_site_evaluation(request: HttpRequest, id: int, data: SiteEvaluationRequest):
    site_evaluation = get_object_or_404(SiteEvaluation, pk=id)

    assert isinstance(data, SiteEvaluationRequest)

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
        site_evaluation.label = lookups.ObservationLabel.objects.get(slug=data.label)
    if data.notes:
        site_evaluation.notes = data.notes
    if data.start_date:
        site_evaluation.start_date = data.start_date
    if data.end_date:
        site_evaluation.end_date = data.end_date
    if data.status:
        site_evaluation.status = data.status

    site_evaluation.save()

    return 200

def get_region_name(country, number, classification):
    # Your implementation of getRegion function here
    # Replace this with the actual implementation of getRegion function
    return getRegion(country, number, classification)


def get_site_model_feature_JSON(id: int, obsevations=False):
    query = (SiteEvaluation.objects.filter(pk=id).values()
        .annotate(
            json=JSONObject(
                site=JSONObject(
                    region=JSONObject(
                        country='region__country',
                        classification='region__classification__slug',
                        number='region__number',
                    ),
                    number='number',
                ),
                configuration='configuration__parameters',
                version='version',
                performer=JSONObject(
                    id='configuration__performer__id',
                    team_name='configuration__performer__description',
                    short_code='configuration__performer__slug',
                ),
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

        # convert to 
        region = data['site']['region']
        region_name = getRegion(region['country'], region['number'], region['classification'])
        site_id = f'{region_name}_{str(data["site"]["number"]).zfill(3)}'
        version = data['version']
        output = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "type": "site",
                        "region_id": region_name,
                        "site_id": site_id,
                        "version": version,
                        "status": data['status'],
                        "score": data['score'],
                        "start_date": None if data['start_date'] is None else datetime.fromisoformat(data['start_date']).strftime('%Y-%m-%d'),
                        "end_date": None if data['end_date'] is None else datetime.fromisoformat(data['end_date']).strftime('%Y-%m-%d'),
                        "model_content": "annotation",
                        "originator": data["performer"]["short_code"],
                    },
                    "geometry": data['geom']
                }
            ]
        }
        return output, site_id
    return None, None

@router.get('/{id}/download')
def download_annotations(request: HttpRequest, id: int):
    output, site_id = get_site_model_feature_JSON(id)
    if output is not None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            json_data = json.dumps(output).encode('utf-8')
            temp_file.write(json_data)

        # Return the temporary file for download
        with open(temp_file.name, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            response["Content-Disposition"] = f"attachment; filename={site_id}.json"

            return response
    # TODO: Some Better Error response
    return 500, 'Unable to export data'
        
