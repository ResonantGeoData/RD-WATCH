import sys
from datetime import datetime

import iso3166
from ninja import Field, FilterSchema, Query, Router, Schema

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.paginator import Paginator
from django.db.models import Count, Max, Min, Q, QuerySet
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest
from rest_framework.settings import api_settings

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SiteEvaluation
from rdwatch.schemas.common import BoundingBoxSchema, TimeRangeSchema

from .performer import PerformerSchema

router = Router()


class SiteEvaluationSchema(Schema):
    id: int
    site: dict
    configuration: dict
    performer: PerformerSchema
    score: float
    timestamp: int
    timerange: TimeRangeSchema
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
    timerange: TimeRangeSchema
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
        timemin=Min('observations__timestamp'),
        timemax=Max('observations__timestamp'),
    ).aggregate(
        count=Count('pk'),
        timerange=JSONObject(
            min=ExtractEpoch(Min('timemin')),
            max=ExtractEpoch(Max('timemax')),
        ),
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
        timemin=Min('observations__timestamp'),
        timemax=Max('observations__timestamp'),
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
