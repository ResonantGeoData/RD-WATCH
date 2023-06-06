from datetime import datetime
from typing import Literal
from urllib.parse import urlencode

import mercantile

from django.contrib.gis.db.models.functions import Area, Transform
from django.db import connection
from django.db.models import (
    BooleanField,
    Case,
    Count,
    F,
    Field,
    Func,
    Max,
    Min,
    Q,
    When,
    Window,
)
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponsePermanentRedirect,
    JsonResponse,
)
from django.views.decorators.cache import cache_page
from rest_framework.reverse import reverse

from rdwatch.db.functions import ExtractEpoch, GroupExcludeRowRange
from rdwatch.models import Region, SiteEvaluation, SiteObservation
from rdwatch.models.lookups import Constellation
from rdwatch.utils.raster_tile import get_raster_bbox, get_raster_tile
from rdwatch.utils.satellite_bands import get_bands
from rdwatch.utils.worldview_processed.raster_tile import (
    get_worldview_processed_visual_bbox,
    get_worldview_processed_visual_tile,
)
from rdwatch.utils.worldview_processed.satellite_captures import get_captures


# @cache_page(60 * 60 * 24 * 7)  # Cache endpoint response for 1 week
def vector_tile(
    request: HttpRequest,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if z is None or x is None or y is None:
        raise ValueError()

    envelope = Func(z, x, y, function='ST_TileEnvelope')
    intersects = Q(
        Func(
            'geom',
            envelope,
            function='ST_Intersects',
            output_field=BooleanField(),
        )
    )
    mvtgeom = Func(
        'geom',
        envelope,
        function='ST_AsMVTGeom',
        output_field=Field(),
    )

    evaluations_queryset = (
        SiteEvaluation.objects.filter(intersects)
        .values()
        .alias(observation_count=Count('observations'))
        .annotate(
            id=F('pk'),
            mvtgeom=mvtgeom,
            configuration_id=F('configuration_id'),
            label=F('label_id'),
            timestamp=ExtractEpoch('timestamp'),
            timemin=ExtractEpoch(Min('observations__timestamp')),
            timemax=ExtractEpoch(Max('observations__timestamp')),
            performer_id=F('configuration__performer_id'),
            region_id=F('region_id'),
            groundtruth=Case(
                When(
                    Q(configuration__performer__slug='TE') & Q(score=1),
                    True,
                ),
                default=False,
            ),
            site_polygon=Case(
                When(
                    observation_count=0,
                    then=True,
                ),
                default=False,
            ),
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
            id=F('pk'),
            mvtgeom=mvtgeom,
            configuration_id=F('siteeval__configuration_id'),
            site_number=F('siteeval__number'),
            label=F('label_id'),
            area=Area(Transform('geom', srid=6933)),
            timemin=ExtractEpoch('timestamp'),
            timemax=ExtractEpoch(
                Window(
                    expression=Min('timestamp'),
                    partition_by=[F('siteeval')],
                    frame=GroupExcludeRowRange(start=0, end=None),
                    order_by='timestamp',  # type: ignore
                ),
            ),
            performer_id=F('siteeval__configuration__performer_id'),
            region_id=F('siteeval__region_id'),
            groundtruth=Case(
                When(
                    Q(siteeval__configuration__performer__slug='TE')
                    & Q(siteeval__score=1),
                    True,
                ),
                default=False,
            ),
        )
    )
    (
        observations_sql,
        observations_params,
    ) = observations_queryset.query.sql_with_params()

    regions_queryset = (
        Region.objects.filter(intersects)
        .values()
        .annotate(
            id=F('pk'),
            mvtgeom=mvtgeom,
        )
    )
    (
        regions_sql,
        regions_params,
    ) = regions_queryset.query.sql_with_params()

    sql = f"""
        WITH
            evaluations AS ({evaluations_sql}),
            observations AS ({observations_sql}),
            regions AS ({regions_sql})
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
            ||
            (
                SELECT ST_AsMVT(regions.*, 'regions', 4096, 'mvtgeom', 'id')
                FROM regions
            )
        )
    """
    params = evaluations_params + observations_params + regions_params

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    tile = row[0]

    return HttpResponse(
        tile,
        content_type='application/octet-stream',
        status=200 if tile else 204,
    )


def get_satelliteimage_raster(
    request: HttpRequest,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    request_type: Literal['tile', 'bbox'] = 'tile'
    if (
        'constellation' not in request.GET
        or 'timestamp' not in request.GET
        or 'spectrum' not in request.GET
        or 'level' not in request.GET
    ):
        return HttpResponseBadRequest()

    bbox = None
    format = None
    if x is None and y is None and z is None:  # Bbox image request
        request_type = 'bbox'
        if 'bbox' not in request.GET or 'format' not in request.GET:
            return HttpResponseBadRequest()

        format = request.GET['format']
        bbox_strings = request.GET['bbox'].split(',')
        if len(bbox_strings) != 4:
            return HttpResponseBadRequest()
        bbox = (
            float(bbox_strings[0]),
            float(bbox_strings[1]),
            float(bbox_strings[2]),
            float(bbox_strings[3]),
        )
    else:
        bounds = mercantile.bounds(x, y, z)
        format = 'WEBP'
        bbox = (bounds.west, bounds.south, bounds.east, bounds.north)

    constellation = Constellation(slug=request.GET['constellation'])
    timestamp = datetime.fromisoformat(str(request.GET['timestamp']))
    level = request.GET['level']
    spectrum = request.GET['spectrum']

    # Convert generator to list so we can iterate over it multiple times
    bands = list(get_bands(constellation, timestamp, bbox))

    # Filter bands by requested processing level and spectrum
    bands = [
        band
        for band in bands
        if (band.level.slug, band.spectrum.slug) == (level, spectrum)
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
    bands.sort(key=lambda band: band.uri.lower().endswith('.tif'), reverse=True)

    if precise_timestamp == timestamp:
        if request_type == 'bbox':
            tile = get_raster_bbox(bands[0].uri, bbox, format)
        else:
            tile = get_raster_tile(bands[0].uri, z, x, y)
        return HttpResponse(
            tile,
            content_type=f'image/{format}',
            status=200,
        )

    query_params = {
        **request.GET.dict(),
        'timestamp': datetime.isoformat(precise_timestamp),
    }
    if request_type == 'bbox':
        return HttpResponsePermanentRedirect(
            reverse('satellite-bbox') + f'?{urlencode(query_params)}'
        )
    else:
        return HttpResponsePermanentRedirect(
            reverse('satellite-tiles', args=[z, x, y]) + f'?{urlencode(query_params)}'
        )


@cache_page(60 * 60 * 24 * 365)
def satelliteimage_raster_bbox(
    request: HttpRequest,
):
    return get_satelliteimage_raster(request)


@cache_page(60 * 60 * 24 * 365)
def satelliteimage_raster_tile(
    request: HttpRequest,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if z is None or x is None or y is None:
        raise ValueError()
    return get_satelliteimage_raster(request, z, x, y)


def get_satelliteimage_visual(
    request: HttpRequest,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if 'timestamp' not in request.GET:
        return HttpResponseBadRequest()

    request_type: Literal['tile', 'bbox'] = 'tile'
    bbox = None
    format = None
    if x is None and y is None and z is None:  # Bbox image request
        request_type = 'bbox'
        if 'format' not in request.GET or 'bbox' not in request.GET:
            return HttpResponseBadRequest()

        format = request.GET['format']
        bbox_strings = request.GET['bbox'].split(',')
        if len(bbox_strings) != 4:
            return HttpResponseBadRequest()
        bbox = (
            float(bbox_strings[0]),
            float(bbox_strings[1]),
            float(bbox_strings[2]),
            float(bbox_strings[3]),
        )
    else:
        bounds = mercantile.bounds(x, y, z)
        format = 'WEBP'
        bbox = (bounds.west, bounds.south, bounds.east, bounds.north)
    timestamp = datetime.fromisoformat(str(request.GET['timestamp']))
    captures = get_captures(timestamp, bbox)
    if not captures:
        return HttpResponseNotFound()

    # Get timestamp closest to the requested timestamp
    closest_capture = min(captures, key=lambda band: abs(band.timestamp - timestamp))

    # If the timestamp provided by the user is *exactly* the timestamp of the retrieved
    # band, return the raster data for it. Otherwise, redirect back to this same view
    # with the exact timestamp as a parameter so that this behavior is triggered during
    # that request. This is done to facilitate caching of the raster data.
    if closest_capture.timestamp == timestamp:
        if request_type == 'bbox':
            tile = get_worldview_processed_visual_bbox(closest_capture, bbox, format)
        else:
            tile = get_worldview_processed_visual_tile(closest_capture, z, x, y)
        return HttpResponse(
            tile,
            content_type=f'image/{format}',
            status=200,
        )

    query_params = {
        **request.GET.dict(),
        'timestamp': datetime.isoformat(closest_capture.timestamp),
    }
    if request_type == 'bbox':
        return HttpResponsePermanentRedirect(
            reverse('satellite-visual-bbox') + f'?{urlencode(query_params)}'
        )
    else:
        return HttpResponsePermanentRedirect(
            reverse('satellite-visual-tiles', args=[z, x, y])
            + f'?{urlencode(query_params)}'
        )


@cache_page(60 * 60 * 24 * 365)
def satelliteimage_visual_bbox(
    request: HttpRequest,
):
    return get_satelliteimage_visual(request)


@cache_page(60 * 60 * 24 * 365)
def satelliteimage_visual_tile(
    request: HttpRequest,
    z: int | None = None,
    x: int | None = None,
    y: int | None = None,
):
    if z is None or x is None or y is None:
        raise ValueError()
    return get_satelliteimage_visual(request, z, x, y)


@cache_page(60 * 60 * 24 * 365)
def satelliteimage_time_list(request: HttpRequest):
    if (
        'constellation' not in request.GET
        or 'level' not in request.GET
        or 'spectrum' not in request.GET
        or 'start_timestamp' not in request.GET
        or 'end_timestamp' not in request.GET
        or 'bbox' not in request.GET
    ):
        return HttpResponseBadRequest()

    constellation = Constellation(slug=request.GET['constellation'])
    spectrum = request.GET['spectrum']
    level = request.GET['level']

    start_timestamp = datetime.fromisoformat(str(request.GET['start_timestamp']))
    end_timestamp = datetime.fromisoformat(str(request.GET['end_timestamp']))

    timebuffer = (end_timestamp - start_timestamp) / 2
    timestamp = start_timestamp + timebuffer

    bbox_strings = request.GET['bbox'].split(',')
    if len(bbox_strings) != 4:
        return HttpResponseBadRequest()
    bbox = (
        float(bbox_strings[0]),
        float(bbox_strings[1]),
        float(bbox_strings[2]),
        float(bbox_strings[3]),
    )

    # Get all image bands within the given time range and requested constellation/bbox
    bands = list(get_bands(constellation, timestamp, bbox, timebuffer))

    # Filter bands by requested processing level and spectrum
    bands = [
        band
        for band in bands
        if (band.level.slug, band.spectrum.slug) == (level, spectrum)
    ]

    timestamps_set = {band.timestamp for band in bands}
    timestamps = [t for t in timestamps_set]
    timestamps.sort()

    return JsonResponse(timestamps, safe=False)


@cache_page(60 * 60 * 24 * 365)
def satelliteimage_visual_time_list(request: HttpRequest):
    if (
        'start_timestamp' not in request.GET
        or 'end_timestamp' not in request.GET
        or 'bbox' not in request.GET
    ):
        return HttpResponseBadRequest()

    start_timestamp = datetime.fromisoformat(str(request.GET['start_timestamp']))
    end_timestamp = datetime.fromisoformat(str(request.GET['end_timestamp']))

    timebuffer = (end_timestamp - start_timestamp) / 2
    timestamp = start_timestamp + timebuffer

    bbox_strings = request.GET['bbox'].split(',')
    if len(bbox_strings) != 4:
        return HttpResponseBadRequest()
    bbox = (
        float(bbox_strings[0]),
        float(bbox_strings[1]),
        float(bbox_strings[2]),
        float(bbox_strings[3]),
    )

    captures = get_captures(timestamp, bbox, timebuffer)

    return JsonResponse([capture.timestamp for capture in captures], safe=False)


# Additional endpoint that returns worldview and satellite images with data about images
@cache_page(60 * 60 * 24 * 365)
def all_satellite_timestamps(request: HttpRequest):
    if (
        'constellation' not in request.GET
        or 'level' not in request.GET
        or 'spectrum' not in request.GET
        or 'start_timestamp' not in request.GET
        or 'end_timestamp' not in request.GET
        or 'bbox' not in request.GET
    ):
        return HttpResponseBadRequest()

    constellation = Constellation(slug=request.GET['constellation'])
    spectrum = request.GET['spectrum']
    level = request.GET['level']

    start_timestamp = datetime.fromisoformat(str(request.GET['start_timestamp']))
    end_timestamp = datetime.fromisoformat(str(request.GET['end_timestamp']))

    timebuffer = (end_timestamp - start_timestamp) / 2
    timestamp = start_timestamp + timebuffer

    bbox_strings = request.GET['bbox'].split(',')
    if len(bbox_strings) != 4:
        return HttpResponseBadRequest()
    bbox = (
        float(bbox_strings[0]),
        float(bbox_strings[1]),
        float(bbox_strings[2]),
        float(bbox_strings[3]),
    )

    # Get all image bands within the given time range and requested constellation/bbox
    bands = list(get_bands(constellation, timestamp, bbox, timebuffer))

    # Filter bands by requested processing level and spectrum
    bands = [
        band
        for band in bands
        if (band.level.slug, band.spectrum.slug) == (level, spectrum)
    ]
    results = []
    for band in bands:
        results.append(
            {
                'timestamp': band.timestamp,
                'cloudcover': band.cloudcover,
                'collection': band.collection,
                'source': 'S2',
            }
        )
    timestamps_set = {band.timestamp for band in bands}
    timestamps = [t for t in timestamps_set]
    timestamps.sort()
    captures = get_captures(timestamp, bbox, timebuffer)
    for capture in captures:
        results.append(
            {
                'timestamp': capture.timestamp,
                'cloudcover': capture.cloudcover,
                'collection': capture.collection,
                'source': 'WorldView',
            }
        )
    results.sort(key=lambda d: d['timestamp'])
    return JsonResponse(results, safe=False)
