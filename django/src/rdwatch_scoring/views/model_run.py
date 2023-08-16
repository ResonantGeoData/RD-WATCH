from ninja import FilterSchema, Query, Schema
from ninja.errors import ValidationError
from ninja.pagination import RouterPaginated

from django.contrib.gis.db.models.fields import PolygonField
from django.contrib.gis.db.models.functions import AsGeoJSON
from django.db.models import Aggregate, CharField, Count, F, JSONField, Max, Min, Value
from django.db.models.functions import Cast, Concat, JSONObject, NullIf, Upper
from django.http import HttpRequest

from rdwatch.db.functions import AggregateArraySubquery, ExtractEpoch
from rdwatch.schemas.common import TimeRangeSchema
from rdwatch.views.performer import PerformerSchema
from rdwatch.views.region import RegionSchema
from rdwatch_scoring.models import EvaluationRun

router = RouterPaginated()


class TimeRangeJSON(NullIf):
    """Represents the min/max time of a field as JSON"""

    def __init__(self, min, max, performer, site_originator):
        json = JSONObject(
            min=ExtractEpoch(Min(min, filter=F(performer) == F(site_originator))),
            max=ExtractEpoch(Max(max, filter=F(performer) == F(site_originator))),
        )
        null = Value({'min': None, 'max': None}, output_field=JSONField())
        return super().__init__(json, null)


class ModelRunFilterSchema(FilterSchema):
    performer: str | None
    region: str | None


class BoundingBoxPolygon(Aggregate):
    """Gets the WGS-84 bounding box of a geometry stored in Web Mercator coordinates"""

    template = 'ST_Extent(%(expressions)s)'
    arity = 1
    output_field = PolygonField()  # type: ignore


class BoundingBoxGeoJSON(Cast):
    """Gets the GeoJSON bounding box of a geometry in Web Mercator coordinates"""

    def __init__(self, field):
        bbox = BoundingBoxPolygon(field)
        json_str = AsGeoJSON(bbox)
        return super().__init__(json_str, JSONField())


class HyperParametersDetailSchema(Schema):
    id: str
    title: str
    region: RegionSchema | None = None
    performer: PerformerSchema
    # parameters: dict
    numsites: int
    # downloading: int | None = None
    score: float | None = None
    timestamp: int | None = None
    timerange: TimeRangeSchema | None = None
    bbox: dict | None
    ground_truth: bool
    # created: datetime
    expiration_time: str | None = None
    evaluation: int | None = None
    evaluation_run: int | None = None


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
    return (
        EvaluationRun.objects.select_related('site', 'observation')
        .order_by(
            'start_datetime',
        )
        .annotate(
            json=JSONObject(
                id='pk',
                title=Concat(
                    F('performer'),
                    Value('_'),
                    F('region'),
                    Value('_'),
                    F('evaluation_number'),
                    Value('_'),
                    F('evaluation_run_number'),
                    output_field=CharField(),
                ),
                performer=JSONObject(
                    id=Value(-1), team_name='performer', short_code=Upper('performer')
                ),
                region=JSONObject(id=Value(-1), name='region'),
                score=None,
                numsites=Count('site__site_id', filter=F('performer') == F('site__originator'), distinct=True),
                evaluation='evaluation_number',
                evaluation_run='evaluation_run_number',
                timerange=TimeRangeJSON(
                    'site__start_date', 'site__end_date', 'performer', 'site_originator'
                ),
                timestamp=ExtractEpoch('start_datetime'),
                ground_truth=False,
                # timerange=TimeRangeJSON('evaluations__observations__timestamp'),
                bbox=BoundingBoxGeoJSON('site__observation__geometry'),
            )
        )
    )


@router.get('/', response={200: HyperParametersListSchema})
def list_model_runs(
    request: HttpRequest,
    filters: ModelRunFilterSchema = Query(...),  # noqa: B008
    limit: int = 25,
    page: int = 1,
):
    queryset = get_queryset()
    queryset = filters.filter(queryset=queryset)

    if page < 1 or (not limit and page != 1):
        raise ValidationError(f"Invalid page '{page}'")

    # Calculate total number of model runs prior to paginating queryset
    total_model_run_count = queryset.count()

    subquery = queryset[(page - 1) * limit : page * limit] if limit else queryset
    aggregate = queryset.defer('json').aggregate(
        timerange=TimeRangeJSON(
            'site__start_date', 'site__end_date', 'performer', 'site_originator'
        ),
        results=AggregateArraySubquery(subquery.values('json')),
    )

    aggregate['count'] = total_model_run_count

    if filters.region is not None:
        aggregate |= queryset.defer('json').aggregate(
            # Use the region polygon for the bbox if it exists.
            # Otherwise, fall back on the site polygon.
            bbox=BoundingBoxGeoJSON('site__observation__geometry'),
        )

    return 200, aggregate
