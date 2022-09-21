from datetime import datetime
from urllib.parse import urlencode

import mercantile

from django.db import connection
from django.db.models import BooleanField, F, Field, Func, Max, Min, Q, RowRange, Window
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponsePermanentRedirect,
)
from django.views.decorators.cache import cache_page
from rest_framework.reverse import reverse

from rdwatch.db.functions import ExtractEpoch
from rdwatch.models import SiteEvaluation, SiteObservation
from rdwatch.models.lookups import Constellation
from rdwatch.utils.raster_tile import get_raster_tile
from rdwatch.utils.satellite_bands import get_bands


def vector_tile(
    request: HttpRequest,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if z is None or x is None or y is None:
        raise ValueError()

    envelope = Func(z, x, y, function="ST_TileEnvelope")
    intersects = Q(
        Func(
            "geom",
            envelope,
            function="ST_Intersects",
            output_field=BooleanField(),
        )
    )
    mvtgeom = Func(
        "geom",
        envelope,
        function="ST_AsMVTGeom",
        output_field=Field(),
    )

    evaluations_queryset = (
        SiteEvaluation.objects.filter(intersects)
        .values()
        .annotate(
            id=F("pk"),
            mvtgeom=mvtgeom,
            configuration=F("configuration_id"),
            timestamp=ExtractEpoch("timestamp"),
            timemin=ExtractEpoch(Min("observations__timestamp")),
            timemax=ExtractEpoch(Max("observations__timestamp")),
        )
    )
    (
        evaluations_sql,
        evaluations_params,
    ) = evaluations_queryset.query.sql_with_params()

    observations_queryset = (
        SiteObservation.objects.filter(intersects)
        .values()
        .annotate(
            id=F("pk"),
            mvtgeom=mvtgeom,
            evaluation=F("siteeval_id"),
            label=F("label_id"),
            timemin=ExtractEpoch("timestamp"),
            timemax=ExtractEpoch(
                Window(
                    expression=Max("timestamp"),
                    partition_by=[F("siteeval")],
                    frame=RowRange(start=0, end=1),
                    order_by="timestamp",  # type: ignore
                ),
            ),
        )
    )
    (
        observations_sql,
        observations_params,
    ) = observations_queryset.query.sql_with_params()

    sql = f"""
        WITH
            evaluations AS ({evaluations_sql}),
            observations AS ({observations_sql})
        SELECT (
            (
                SELECT ST_AsMVT(evaluations.*, 'sites', 4096, 'mvtgeom', 'id')
                FROM evaluations
            )
            ||
            (
                SELECT ST_AsMVT(observations.*, 'observations', 4096, 'mvtgeom', 'id')
                FROM observations
            )
        )
    """
    params = evaluations_params + observations_params

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    tile = row[0]

    return HttpResponse(
        tile,
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

    # Convert generator to list so we can iterate over it multiple times
    bands = list(get_bands(constellation, timestamp, bbox))

    # Filter bands by requested processing level and spectrum
    bands = [
        band
        for band in bands
        if (band.level.slug, band.spectrum.slug)
        == (request.GET["level"], request.GET["spectrum"])
    ]

    if not bands:
        return HttpResponseNotFound()

    # Get timestamp closest to the requested timestamp
    precise_timestamp = min(
        bands, key=lambda band: abs(band.timestamp - timestamp)
    ).timestamp

    # Filter out any bands that don't have that timestamp
    bands = [band for band in bands if band.timestamp == precise_timestamp]

    # Sort bands so that bands in TIF format come first (TIFs are cheaper to tile
    # and are preferred over other formats when possible)
    bands.sort(key=lambda band: band.uri.lower().endswith(".tif"), reverse=True)

    # If the timestamp provided by the user is *exactly* the timestamp of the retrieved
    # band, return the raster data for it. Otherwise, redirect back to this same view
    # with the exact timestamp as a parameter so that this behavior is triggered during
    # that request. This is done to facilitate caching of the raster data.
    if precise_timestamp == timestamp:
        tile = get_raster_tile(bands[0].uri, z, x, y)
        return HttpResponse(
            tile,
            content_type="image/webp",
            status=200,
        )

    query_params = {
        **request.GET.dict(),
        "timestamp": datetime.isoformat(precise_timestamp),
    }

    return HttpResponsePermanentRedirect(
        reverse("satellite-tiles", args=[z, x, y]) + f"?{urlencode(query_params)}"
    )
