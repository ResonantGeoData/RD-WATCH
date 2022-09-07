from datetime import datetime

from django.db import connection
from django.db.models import BooleanField, DateTimeField, F, Field, Func, Q, Value
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponsePermanentRedirect,
)
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from rdwatch.db.functions import GistDistance
from rdwatch.models import SatelliteImage, SiteEvaluation, SiteObservation
from rdwatch.utils.raster_tile import get_raster_tile
from rest_framework.reverse import reverse


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
def satelliteimage_raster_redirect(
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
    satimg = (
        SatelliteImage.objects.filter(
            constellation__slug=request.GET["constellation"],
            spectrum__slug=request.GET["spectrum"],
            level__slug=request.GET["level"],
        )
        .alias(
            timedistance=GistDistance(
                F("timestamp"),
                Value(
                    datetime.fromisoformat(str(request.GET["timestamp"])),
                    output_field=DateTimeField(),
                ),
            )
        )
        .order_by("timedistance")
        .first()
    )
    if satimg is None:
        return HttpResponseNotFound()
    return HttpResponsePermanentRedirect(
        reverse("satellite-tiles", args=[satimg.pk, z, x, y]),
    )


# @cache_page(60 * 60 * 24 * 365)
def satelliteimage_raster_tile(
    request: HttpRequest,
    pk: int | None = None,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if pk is None or z is None or x is None or y is None:
        raise ValueError()
    satimg = get_object_or_404(SatelliteImage, pk=pk)
    tile = get_raster_tile(satimg.uri, z, x, y)
    return HttpResponse(
        tile,
        content_type="image/webp",
        status=200,
    )
