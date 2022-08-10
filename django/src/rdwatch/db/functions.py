from django.contrib.gis.db.models import PolygonField
from django.db.models import Func, IntegerField


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


class RasterNumBands(Func):
    """Returns the number of bands in a raster."""

    function = "ST_NumBands"
    output_field: IntegerField = IntegerField()
