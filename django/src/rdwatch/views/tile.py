from datetime import datetime
from urllib.parse import urlencode

import mercantile

from django.db import connection
from django.db.models import BooleanField, Field, Func, Q
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponsePermanentRedirect,
)
from django.views.decorators.cache import cache_page
from rest_framework.reverse import reverse

from rdwatch.models import SiteEvaluation, SiteObservation
from rdwatch.models.lookups import Constellation
from rdwatch.utils.raster_tile import get_raster_tile
from rdwatch.utils.satellite_bands import Band, get_bands


def site_evaluation_vector_tile(
    request: HttpRequest,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if z is None or x is None or y is None:
        raise ValueError()
    envelope = Func(z, x, y, function="ST_TileEnvelope")
    intersects = Func(
        "geom",
        envelope,
        function="ST_Intersects",
        output_field=BooleanField(),
    )
    mvtgeom = Func("geom", envelope, function="ST_AsMVTGeom", output_field=Field())
    ctequeryset = (
        SiteEvaluation.objects.filter(Q(intersects))
        .annotate(mvtgeom=mvtgeom)
        .values("id", "mvtgeom", "score")
    )
    ctesql, cteparams = ctequeryset.query.sql_with_params()
    with connection.cursor() as cursor:
        sql = f"""
        WITH cte AS ({ctesql})
        SELECT ST_AsMVT(cte.*, 'default', 4096, 'mvtgeom', 'id') FROM cte
        """
        cursor.execute(sql, cteparams)
        row = cursor.fetchone()
    tile = row[0]
    return HttpResponse(
        row[0],
        content_type="application/octet-stream",
        status=200 if tile else 204,
    )


# @cache_page(60 * 60 * 24 * 365)
def site_observation_vector_tile(
    request: HttpRequest,
    pk: int | None = None,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if pk is None or z is None or x is None or y is None:
        raise ValueError()
    envelope = Func(z, x, y, function="ST_TileEnvelope")
    intersects = Func(
        "geom",
        envelope,
        function="ST_Intersects",
        output_field=BooleanField(),
    )
    mvtgeom = Func("geom", envelope, function="ST_AsMVTGeom", output_field=Field())
    ctequeryset = (
        SiteObservation.objects.filter(siteeval=pk)
        .filter(Q(intersects))
        .annotate(mvtgeom=mvtgeom)
        .values("id", "mvtgeom", "score")
    )
    ctesql, cteparams = ctequeryset.query.sql_with_params()
    with connection.cursor() as cursor:
        sql = f"""
        WITH cte AS ({ctesql})
        SELECT ST_AsMVT(cte.*, 'default', 4096, 'mvtgeom', 'id') FROM cte
        """
        cursor.execute(sql, cteparams)
        row = cursor.fetchone()
    tile = row[0]
    return HttpResponse(
        row[0],
        content_type="application/octet-stream",
        status=200 if tile else 204,
    )


@cache_page(60 * 60 * 24 * 365)
def satelliteimage_raster_tile(
    request: HttpRequest,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if z is None or x is None or y is None:
        raise ValueError()
    if (
        "constellation" not in request.GET
        or "level" not in request.GET
        or "timestamp" not in request.GET
        or "spectrum" not in request.GET
    ):
        return HttpResponseBadRequest()

    constellation = Constellation(slug=request.GET["constellation"])
    timestamp = datetime.fromisoformat(str(request.GET["timestamp"]))

    # Calculate the bounding box from the given x, y, z parameters
    bounds = mercantile.bounds(x, y, z)
    bbox = (bounds.west, bounds.south, bounds.east, bounds.north)

    bands = get_bands(constellation, timestamp, bbox)

    try:
        band: Band = next(bands)
    except StopIteration:
        return HttpResponseNotFound()

    # If the timestamp provided by the user is *exactly* the timestamp of the retrieved
    # band, return the raster data for it. Otherwise, redirect back to this same view
    # with the exact timestamp as a parameter so that this behavior is triggered during
    # that request. This is done to facilitate caching of the raster data.
    if band.timestamp == timestamp:
        tile = get_raster_tile(band.uri, z, x, y)
        return HttpResponse(
            tile,
            content_type="image/webp",
            status=200,
        )

    query_params = {
        **request.GET.dict(),
        "timestamp": datetime.isoformat(band.timestamp),
    }

    return HttpResponsePermanentRedirect(
        reverse("satellite-tiles", args=[z, x, y]) + f"?{urlencode(query_params)}"
    )
