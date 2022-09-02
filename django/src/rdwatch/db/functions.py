from django.contrib.gis.db.models import PolygonField
from django.db.models import (
    Aggregate,
    BinaryField,
    BooleanField,
    Func,
    Lookup,
    Q,
    Value,
)


class GistDistance(Lookup):
    lookup_name = "distance"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <-> %s" % (lhs, rhs), params


class IntersectsTile(Func):
    """Returns `True` if the field intersect a ZXY tile."""

    function = "ST_Intersects"
    output_field: BooleanField = BooleanField()

    def __init__(self, field, z: int, x: int, y: int):
        tile = Func(
            z, x, y, function="ST_TileEnvelope", output_field=PolygonField(srid=3857)
        )
        return super().__init__(field, tile)


class VectorTile(Aggregate):
    """Returns the vector tile at the specified ZXY."""

    function = "ST_AsMVT"
    output_field: BinaryField = BinaryField()

    def __init__(
        self,
        field,
        z: int,
        x: int,
        y: int,
        filter=Q(),
        name="default",
        extent=4096,
        feature_id="pk",
    ):
        envelope = Func(z, x, y, function="ST_TileEnvelope")
        filter &= Q(
            Func(
                field,
                envelope,
                function="ST_Intersects",
                output_field=BooleanField(),
            )
        )
        row = Func(
            feature_id,
            Func(field, envelope, function="ST_AsMVTGeom"),
            function="ROW",
        )
        super().__init__(
            row,
            Value(name),
            Value(extent),
            Value("f2"),
            Value("f1"),
            filter=filter,
        )
