from datetime import datetime, timedelta
from typing import Literal

from pydantic import UUID4

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
from rdwatch.models import ModelRun, Region, SiteEvaluation, SiteObservation

from .model_run import router


def _get_vector_tile_cache_key(
    model_run_id: UUID4, z: int, x: int, y: int, timestamp: datetime
) -> str:
    return '|'.join(
        [
            ModelRun.__name__,
            str(model_run_id),
            'vector-tile',
            str(z),
            str(x),
            str(y),
            str(timestamp),
        ]
    ).replace(' ', '_')


@router.get('/{model_run_id}/vector-tile/{z}/{x}/{y}.pbf/')
def vector_tile(request: HttpRequest, model_run_id: UUID4, z: int, x: int, y: int):
    timestamps: dict[
        Literal[
            'latest_evaluation_timestamp',
            'model_run_timestamp',
        ],
        datetime | None,
    ] = ModelRun.objects.filter(id=model_run_id).aggregate(
        # Get timestamp of most recent site evaluation so we can use it as a cache key
        latest_evaluation_timestamp=Max('evaluations__timestamp'),
        # Also include the timestamp of the model run itself. A model
        # run with no evaluations will use this for the cache key. The
        # `Max()` aggregation has no effect here, but we need to call
        # *some* kind of aggregation function in order for the query to
        # work correctly. This is preferable to making a separate
        # query/round-trip to the DB in order to check for the model
        # run's existence.
        model_run_timestamp=Max('created'),
    )

    # A null value for the model run timestamp indicates that
    # this model run doesn't exist.
    if timestamps['model_run_timestamp'] is None:
        raise Http404()

    latest_timestamp = (
        timestamps['latest_evaluation_timestamp'] or timestamps['model_run_timestamp']
    )

    # Generate a unique cache key based on the model run ID, vector tile coordinates,
    # and the latest timestamp
    cache_key = _get_vector_tile_cache_key(model_run_id, z, x, y, latest_timestamp)

    tile = cache.get(cache_key)

    # Generate the vector tiles and cache them if there's no hit
    if tile is None:
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
            SiteEvaluation.objects.filter(configuration_id=model_run_id)
            .filter(intersects)
            .values()
            .alias(observation_count=Count('observations'))
            .annotate(
                id=F('pk'),
                mvtgeom=mvtgeom,
                configuration_id=F('configuration_id'),
                label=F('label_id'), # Resolves to name instead of ID
                timestamp=ExtractEpoch('timestamp'),
                timemin=ExtractEpoch(Min('observations__timestamp')),
                timemax=ExtractEpoch(Max('observations__timestamp')),
                performer_id=F('configuration__performer_id'),
                region=F('region__name'),
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
            SiteObservation.objects.filter(siteeval__configuration_id=model_run_id)
            .filter(intersects)
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
                region=F('siteeval__region__name'),
                version=F('siteeval__version'),
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
            Region.objects.filter(evaluations__configuration_id=model_run_id)
            .filter(intersects)
            .values()
            .annotate(
                name=F('name'),
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
                    SELECT ST_AsMVT(evaluations.*, %s, 4096, 'mvtgeom', 'id')
                    FROM evaluations
                )
                ||
                (
                    SELECT ST_AsMVT(observations.*, %s, 4096, 'mvtgeom', 'id')
                    FROM observations
                )
                ||
                (
                    SELECT ST_AsMVT(regions.*, %s, 4096, 'mvtgeom', 'id')
                    FROM regions
                )
            )
        """  # noqa: E501
        params = (
            evaluations_params
            + observations_params
            + regions_params
            + (
                f'sites-{model_run_id}',
                f'observations-{model_run_id}',
                f'regions-{model_run_id}',
            )
        )

        with connection.cursor() as cursor:
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
