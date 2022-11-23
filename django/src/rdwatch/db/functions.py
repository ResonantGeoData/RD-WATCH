from django.contrib.gis.db.models.functions import Envelope, Transform
from django.db.models import FloatField, Func, IntegerField, RowRange
from django.db.models.functions import JSONObject  # type: ignore


class ExtractEpoch(Func):
    """Represents the DateTimeField as a UNIX timestamp"""

    output_field: IntegerField = IntegerField()
    template = "EXTRACT(epoch FROM %(expressions)s)::bigint"
    arity = 1


class BoundingBox(JSONObject):
    """Gets the WGS-84 bounding box of a geometry"""

    def __init__(self, field):
        geom = Transform(Envelope(field), 4326)
        return super().__init__(
            xmin=Func(
                geom,
                function="ST_XMin",
                output_field=FloatField(),
            ),
            ymin=Func(
                geom,
                function="ST_YMin",
                output_field=FloatField(),
            ),
            xmax=Func(
                geom,
                function="ST_XMax",
                output_field=FloatField(),
            ),
            ymax=Func(
                geom,
                function="ST_YMax",
                output_field=FloatField(),
            ),
        )


class GroupExcludeRowRange(RowRange):
    """A RowRange that excludes the current group

    https://www.postgresql.org/docs/current/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS
    """

    template = RowRange.template + " EXCLUDE GROUP"
