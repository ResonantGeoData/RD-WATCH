from datetime import datetime, timedelta
from typing import Literal

from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Area, Transform
from django.core.cache import cache
from django.db import connections
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
    Value,
    When,
    Window,
)
from django.http import Http404, HttpRequest, HttpResponse

from rdwatch.db.functions import ExtractEpoch, GroupExcludeRowRange
from rdwatch_scoring.models_file import EvaluationRun, Site, Observation
from rdwatch_scoring.models import HyperParameters, Region

from .model_run import router

def _get_vector_tile_cache_key(
    evaluation_run_uuid: int, z: int, x: int, y: int, timestamp: datetime
) -> str:
    return '|'.join(
        [
            HyperParameters.__name__,
            str(evaluation_run_uuid),
            'vector-tile',
            str(z),
            str(x),
            str(y),
            str(timestamp),
        ]
    ).replace(' ', '_')


@router.get('/{evaluation_run_uuid}/vector-tile/{z}/{x}/{y}.pbf/')
def vector_tile(request: HttpRequest, evaluation_run_uuid, z: int, x: int, y: int):

    latest_timestamp = EvaluationRun.objects.get(pk=evaluation_run_uuid).start_datetime

    # Generate a unique cache key based on the model run ID, vector tile coordinates,
    # and the latest timestamp
    cache_key = _get_vector_tile_cache_key(
        evaluation_run_uuid, z, x, y, latest_timestamp
    )

    tile = cache.get(cache_key)

    # Generate the vector tiles and cache them if there's no hit
    if tile is None:
        envelope = Func(z, x, y, function='ST_TileEnvelope')
        intersects = Q(
            Func(
                'transformedgeom',
                envelope,
                function='ST_Intersects',
                output_field=BooleanField(),
            )
        )
        transform = Func(
            'geomfromtext',
            3857,
            function='ST_Transform',
            output_field=Field()
        )
        mvtgeom = Func(
            'transformedgeom',
            envelope,
            function='ST_AsMVTGeom',
            output_field=Field(),
        )
        geomfromuniongeometrytext = Func(
            'union_geometry',
            4326,
            function='ST_GeomFromText',
            output_field=Field()
        )
        geomfromobservationtext = Func(
            'geometry',
            4326,
            function='ST_GeomFromText',
            output_field=Field()
        )

        site_queryset = (
            Site.objects.filter(evaluation_run_uuid=evaluation_run_uuid)
            .annotate(geomfromtext=geomfromuniongeometrytext)
            .annotate(transformedgeom=transform)
            .filter(intersects)
            .values()
            .annotate(
                id=F('pk'),
                mvtgeom=mvtgeom,
                timemin=ExtractEpoch('start_date'),
                timemax=ExtractEpoch('end_date'),
                performer_id=F('originator'),
                region_id=F('region_id'),
                groundtruth=
                Case(
                    When(
                        Q(originator='te'),
                        True,
                        ),
                    default=False,
                ),
                site_polygon=Value(True, output_field=BooleanField())
            )
        )
        (
            site_sql,
            site_params,
        ) = site_queryset.query.sql_with_params()

        observations_queryset = (
            Observation.objects.filter(site_uuid__evaluation_run_uuid=evaluation_run_uuid)
            .annotate(geomfromtext=geomfromobservationtext)
            .annotate(transformedgeom=transform)
            .filter(intersects)
            .values()
            .annotate(
                mvtgeom=mvtgeom,
                site_number=F('site_uuid__site_id'),
                timemin=ExtractEpoch('date'),
                performer_id=F('site_uuid__originator'),
                region_id=F('site_uuid__region_id'),
                version=F('site_uuid__version'),
                groundtruth=
                Case(
                    When(
                        Q(site_uuid__originator='te'),
                        True,)
                    ,
                    default=False,
                ),
            )
        )
        (
            observations_sql,
            observations_params,
        ) = observations_queryset.query.sql_with_params()

        region_queryset = (
            Region.objects.filter(id__in=site_queryset.values('region_id'))
            .annotate(geomfromtext=geomfromobservationtext)
            .annotate(transformedgeom=transform)
            .filter(intersects)
            .annotate(mvtgeom=mvtgeom)
        )
        (
            region_sql,
            region_params,
        ) = region_queryset.query.sql_with_params()

        sql = f"""
            WITH
                sites AS ({site_sql}),
                observations AS ({observations_sql}),
                regions AS ({region_sql})
            SELECT(
                (
                    SELECT ST_AsMVT(sites.*, %s, 4096, 'mvtgeom')
                    FROM sites
                )
                ||
                (
                    SELECT ST_AsMVT(observations.*, %s, 4096, 'mvtgeom')
                    FROM observations
                )
                ||
                (
                    SELECT ST_AsMVT(regions.*, %s, 4096, 'mvtgeom')
                    FROM regions
                )
            )
        """  # noqa: E501
        params = (
            site_params
            + observations_params
            + region_params
            + (f'sites-{evaluation_run_uuid}',
               f'observations-{evaluation_run_uuid}',
               f'regions-{evaluation_run_uuid}')
        )

        with connections['scoringdb'].cursor() as cursor:
            cursor.execute(sql, params)

            row = cursor.fetchone()
        # What is being returned here?
        tile = row[0]

        # Cache this for 30 days
        cache.set(cache_key, tile.tobytes(), timedelta(days=30).total_seconds())

    return HttpResponse(
        tile,
        content_type='application/octet-stream',
        status=200 if tile else 204,
    )