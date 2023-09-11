from datetime import datetime, timedelta
from typing import Literal

from django.contrib.gis.db.models.functions import Area, Transform
from django.core.cache import cache
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
from django.http import Http404, HttpRequest, HttpResponse

from rdwatch.db.functions import ExtractEpoch, GroupExcludeRowRange
from rdwatch_scoring.models_file import EvaluationRun, Site, Observation
from rdwatch_scoring.models import HyperParameters, SiteEvaluation, SiteObservation, Region

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
                'geomfromtext',
                envelope,
                function='ST_Intersects',
                output_field=BooleanField(),
            )
        )

        mvtgeom = Func(
            'geomfromtext',
            envelope,
            function='ST_AsMVTGeom',
            output_field=Field(),
        )
        geomfromtext = Func(
            'union_geometry',
            function='ST_GeomFromText',
            output_field=Field()
        )
        setsrid = Func(
            'geomfromtext',
            3857,
            function='ST_SetSRID',
            output_field=Field()
        )

        site_queryset = (
            Site.objects.filter(evaluation_run_uuid=evaluation_run_uuid)
            .annotate(
            geomfromtext=geomfromtext
            )
            .annotate(
            geomfromtext=setsrid
            )
            .filter(intersects)
            .annotate(
            mvtgeom=mvtgeom
            )
        )
        (
            site_sql,
            site_params,
        ) = site_queryset.query.sql_with_params()

        observations_queryset = (
            Observation.objects.filter(site_uuid__evaluation_run_uuid=evaluation_run_uuid)
        )
        (
            observations_sql,
            observations_params,
        ) = observations_queryset.query.sql_with_params()
        region_queryset = (
            Region.objects.filter(id__in=site_queryset.values('region'))
        )
        (
            region_sql,
            region_params,
        ) = region_queryset.query.sql_with_params()

        sql = f"""
            WITH
                sites AS ({site_sql})
            SELECT (
                (
                    SELECT ST_AsMVT(sites.*, %s, 4096, 'mvtgeom')
                    FROM sites
                )
            )
        """  # noqa: E501
        params = (
            site_params
            # + observations_params
            # + region_params
            + (f'sites-{evaluation_run_uuid}',)
               # f'observations-{evaluation_run_uuid}',
               # f'regions-{evaluation_run_uuid}')
        )

        with connection.cursor() as cursor:
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
