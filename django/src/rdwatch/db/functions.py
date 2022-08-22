from django.contrib.gis.db.models import PolygonField
from django.contrib.postgres.fields import DecimalRangeField
from django.db.models import Aggregate, BinaryField, Func, IntegerField


class RasterHeight(Func):
    """Returns the height of the raster in pixels."""

    function = "ST_Height"
    output_field: IntegerField = IntegerField()


class RasterWidth(Func):
    """Returns the height of the raster in pixels."""

    function = "ST_Width"
    output_field: IntegerField = IntegerField()


class RasterEnvelope(Func):
    """Returns the bounding box of a raster."""

    function = "ST_Envelope"
    output_field: PolygonField = PolygonField()


class RasterXRange(Func):
    """Returns the range spanned by a raster in the X direction."""

    function = "numrange"
    template = "%(function)s(%(expressions)s::numeric, '()')"
    arg_joiner = "::numeric, "
    output_field: DecimalRangeField = DecimalRangeField()

    def __init__(self, field, **extra):
        box = Func(field, function="Box3D")
        xmin = Func(box, function="ST_XMin")
        xmax = Func(box, function="ST_XMax")
        super().__init__(xmin, xmax, **extra)


class RasterYRange(Func):
    """Returns the range spanned by a raster in the Y direction."""

    function = "numrange"
    template = "%(function)s(%(expressions)s::numeric, '()')"
    arg_joiner = "::numeric, "
    output_field: DecimalRangeField = DecimalRangeField()

    def __init__(self, field, **extra):
        box = Func(field, function="Box3D")
        ymin = Func(box, function="ST_YMin")
        ymax = Func(box, function="ST_YMax")
        super().__init__(ymin, ymax, **extra)


class RasterNumBands(Func):
    """Returns the number of bands in a raster."""

    function = "ST_NumBands"
    output_field: IntegerField = IntegerField()


class VectorTile(Aggregate):
    """Returns the vector tile at the specified ZXY."""

    function = "ST_AsMVT"
    output_field: BinaryField = BinaryField()

    def __init__(self, field, z: int, x: int, y: int, **extra):
        tile_envelope = Func(z, x, y, function="ST_TileEnvelope")
        mvt_geom = Func(field, tile_envelope, function="ST_AsMVTGeom")
        row = Func(mvt_geom, function="ROW")
        super().__init__(row, **extra)
