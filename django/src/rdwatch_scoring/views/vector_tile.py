from datetime import datetime, timedelta

from pydantic import UUID4

from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Area, Transform
from django.core.cache import cache
from django.db import connections
from django.db.models import (
    BooleanField,
    Case,
    F,
    Field,
    Func,
    Min,
    Q,
    Value,
    When,
    Window,
)
from django.db.models.functions import Lower, Replace, Substr
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.db.functions import ExtractEpoch, GroupExcludeRowRange
from rdwatch_scoring.models import EvaluationRun, Observation, Region, Site

from .model_run import router


def _get_vector_tile_cache_key(
    evaluation_run_uuid: UUID4, z: int, x: int, y: int, timestamp: datetime
) -> str:
    return '|'.join(
        [
            Site.__name__,
            str(evaluation_run_uuid),
            'vector-tile',
            str(z),
            str(x),
            str(y),
            str(timestamp),
        ]
    ).replace(' ', '_')


@router.get('/{evaluation_run_uuid}/vector-tile/{z}/{x}/{y}.pbf/')
def vector_tile(
    request: HttpRequest, evaluation_run_uuid: UUID4, z: int, x: int, y: int
):
    evaluation_run = get_object_or_404(EvaluationRun, pk=evaluation_run_uuid)

    latest_timestamp = evaluation_run.start_datetime

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
            'geomfromtext', 3857, function='ST_Transform', output_field=GeometryField()
        )
        mvtgeom = Func(
            'transformedgeom',
            envelope,
            function='ST_AsMVTGeom',
            output_field=Field(),
        )
        geomfromuniongeometrytext = Func(
            'union_geometry', 4326, function='ST_GeomFromText', output_field=Field()
        )
        geomfromobservationtext = Func(
            'geometry', 4326, function='ST_GeomFromText', output_field=Field()
        )

        site_queryset = (
            Site.objects.filter(evaluation_run_uuid=evaluation_run_uuid)
            .alias(geomfromtext=geomfromuniongeometrytext)
            .alias(transformedgeom=transform)
            .filter(intersects)
            .values()
            .annotate(
                id=F('site_id'),
                mvtgeom=mvtgeom,
                configuration_id=F('evaluation_run_uuid'),
                label=Case(
                    When(
                        Q(status_annotated__isnull=False),
                        Lower(Replace('status_annotated', Value(' '), Value('_'))),
                    ),
                    default=Value('unknown'),
                ),  # This needs a version to be scoring coloring,
                # but that needs some coordination with kitware
                timestamp=ExtractEpoch('start_date'),
                timemin=ExtractEpoch('start_date'),
                timemax=ExtractEpoch('end_date'),
                performer_id=F('originator'),
                region=F('region_id'),
                groundtruth=Case(
                    When(
                        Q(originator='te'),
                        True,
                    ),
                    default=False,
                ),
                site_polygon=Value(False, output_field=BooleanField()),
            )
        )
        (
            site_sql,
            site_params,
        ) = site_queryset.query.sql_with_params()

        observations_queryset = (
            Observation.objects.filter(
                site_uuid__evaluation_run_uuid=evaluation_run_uuid
            )
            .alias(geomfromtext=geomfromobservationtext)
            .alias(transformedgeom=transform)
            .filter(intersects)
            .values()
            .annotate(
                id=F('uuid'),
                timestamp=F('date'),
                mvtgeom=mvtgeom,
                configuration_id=F('site_uuid__evaluation_run_uuid'),
                site_number=Substr(F('site_uuid__site_id'), 9),  # pos is 1 indexed
                label=Case(
                    When(
                        Q(phase__isnull=False),
                        Lower(Replace('phase', Value(' '), Value('_'))),
                    ),
                    default=Value('unknown'),
                ),  # This should be an ID, on client side can make it understand this
                area=Area(Transform('transformedgeom', srid=6933)),
                siteeval_id=F('site_uuid'),
                timemin=ExtractEpoch('date'),
                timemax=ExtractEpoch(
                    Window(
                        expression=Min('date'),
                        partition_by=[F('site_uuid')],
                        frame=GroupExcludeRowRange(start=0, end=None),
                        order_by='date',
                    ),
                ),  # This probably needs to be using the site tables start/end dates
                performer_id=F('site_uuid__originator'),
                region=F('site_uuid__region_id'),
                version=F('site_uuid__version'),
                score=F('confidence_score'),
                groundtruth=Case(
                    When(
                        Q(site_uuid__originator='te'),
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

        region_queryset = (
            Region.objects.filter(id=site_queryset.values('region_id')[:1])
            .alias(geomfromtext=geomfromobservationtext)
            .alias(transformedgeom=transform)
            .filter(intersects)
            .values()
            .annotate(name=F('id'), mvtgeom=mvtgeom)
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
            + (
                f'sites-{evaluation_run_uuid}',
                f'observations-{evaluation_run_uuid}',
                f'regions-{evaluation_run_uuid}',
            )
        )

        with connections['scoringdb'].cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
        tile = row[0]

        # Cache this for 30 days
        cache.set(cache_key, tile.tobytes(), timedelta(days=30).total_seconds())

    return HttpResponse(
        tile,
        content_type='application/octet-stream',
        status=200 if tile else 204,
    )
