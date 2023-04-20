from django.contrib.gis.db.models.fields import PolygonField
from django.contrib.gis.db.models.functions import AsGeoJSON, Envelope, Transform
from django.contrib.postgres.expressions import ArraySubquery  # type: ignore
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    Aggregate,
    FloatField,
    Func,
    IntegerField,
    JSONField,
    Max,
    Min,
    RowRange,
    Value,
)
from django.db.models.functions import JSONObject  # type: ignore
from django.db.models.functions import Cast, NullIf


class ExtractEpoch(Func):
    """Represents the DateTimeField as a UNIX timestamp"""

    output_field: IntegerField = IntegerField()
    template = 'EXTRACT(epoch FROM %(expressions)s)::bigint'
    arity = 1

class GeomArea(JSONObject):
    def __init__(self, field):
        geom = Transform((field), 3086)
        return super().__init__(
            area=Func(
                geom,
                function='ST_Area',
                output_field=FloatField(),
            )
        )

class BoundingBox(JSONObject):
    """Gets the WGS-84 bounding box of a geometry

    This function has been superseded by the
    'rdwatch.db.functions.BoundingBox' class. This legacy
    version has been copied here rather than updating
    the view as this view will likely be removed in the
    future.
    """

    def __init__(self, field):
        geom = Transform(Envelope(field), 4326)
        return super().__init__(
            xmin=Func(
                geom,
                function='ST_XMin',
                output_field=FloatField(),
            ),
            ymin=Func(
                geom,
                function='ST_YMin',
                output_field=FloatField(),
            ),
            xmax=Func(
                geom,
                function='ST_XMax',
                output_field=FloatField(),
            ),
            ymax=Func(
                geom,
                function='ST_YMax',
                output_field=FloatField(),
            ),
        )


class BoundingBoxPolygon(Aggregate):
    """Gets the WGS-84 bounding box of a geometry stored in Web Mercator coordinates"""

    template = 'ST_Transform(ST_SetSRID(ST_Extent(%(expressions)s), 3857), 4326)'
    arity = 1
    output_field = PolygonField()  # type: ignore


class BoundingBoxGeoJSON(Cast):
    """Gets the GeoJSON bounding box of a geometry in Web Mercator coordinates"""

    def __init__(self, field):
        bbox = BoundingBoxPolygon(field)
        json_str = AsGeoJSON(bbox)
        return super().__init__(json_str, JSONField())


class TimeRangeJSON(NullIf):
    """Represents the min/max time of a field as JSON"""

    def __init__(self, field):
        json = JSONObject(
            min=ExtractEpoch(Min(field)),
            max=ExtractEpoch(Max(field)),
        )
        null = Value({'min': None, 'max': None}, output_field=JSONField())
        return super().__init__(json, null)


class AggregateArraySubquery(Max):
    """A hacky way to add a subquery to an aggregate

    Input is passed to 'ArraySubquery'.

    https://docs.djangoproject.com/en/4.1/ref/contrib/postgres/expressions/#arraysubquery-expressions
    """

    def __init__(self, *args, **kwargs):
        null = Value(None, output_field=ArrayField(base_field=JSONField()))
        return super().__init__(null, default=ArraySubquery(*args, **kwargs))


class GroupExcludeRowRange(RowRange):
    """A RowRange that excludes the current group

    https://www.postgresql.org/docs/current/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS
    """

    template = RowRange.template + ' EXCLUDE GROUP'
