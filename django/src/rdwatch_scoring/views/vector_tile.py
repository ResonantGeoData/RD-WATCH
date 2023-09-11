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
from rdwatch_scoring.models_file import EvaluationRun, SiteEvaluationAPL
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
        # my test
        my_queryset = (
            SiteEvaluationAPL.objects.filter(uuid=f"'{evaluation_run_uuid}'")
            .filter(intersects)
            .values()
            .alias(observation_count=Count('observations'))
        )
        #     .annotate(
        #         uuid=F('pk'),
        #         mvtgeom=mvtgeom,
        #         configuration_id=F('evaluation_run_uuid'),
        #         label=F('label_id'),
        #         timestamp=ExtractEpoch('timestamp'),
        #         timemin=ExtractEpoch(Min('observations__timestamp')),
        #         timemax=ExtractEpoch(Max('observations__timestamp')),
        #         performer_id=F('configuration__performer_id'), # no performer_id in HyperParameters
        #         region_id=F('region_id'),
        #         groundtruth=Case(
        #             When(
        #                 Q(configuration__performer__slug='TE') & Q(score=1),
        #                 True,
        #             ),
        #             default=False,
        #         ),
        #         site_polygon=Case(
        #             When(
        #                 observation_count=0,
        #                 then=True,
        #             ),
        #             default=False,
        #         ),
        #     )
        # )
        (
            my_evaluations_sql,
            my_evaluations_params,
        ) = my_queryset.query.sql_with_params()
        print("hi")

        evaluations_queryset = (
            SiteEvaluation.objects.filter(configuration_id=f"'{evaluation_run_uuid}'")
            .filter(intersects)
            .values()
            .alias(observation_count=Count('observations')) #where is observations table?
            .annotate(
                uuid=F('pk'),
                mvtgeom=mvtgeom,
                configuration_id=F('configuration_id'),
                label=F('label_id'),
                timestamp=ExtractEpoch('timestamp'),
                timemin=ExtractEpoch(Min('observations__timestamp')),
                timemax=ExtractEpoch(Max('observations__timestamp')),
                performer_id=F('configuration__performer_id'), # no performer_id in HyperParameters,
                # should it be performer__id?
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
            SiteObservation.objects.filter(
                siteeval__configuration_id=f"'{evaluation_run_uuid}'"
            )
            .filter(intersects)
            .values()
            .annotate(
                uuid=F('pk'),
                mvtgeom=mvtgeom,
                configuration_id=F('siteeval__configuration_id'),  # class SiteObservation.siteeval, Q: id or uuid?
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
            Region.objects.filter(evaluations__configuration_id=f"'{evaluation_run_uuid}'")
            .filter(intersects)
            .values()
            .annotate(
                uuid=F('pk'),
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
                    SELECT ST_AsMVT(evaluations.*, %s, 4096, 'mvtgeom', 'uuid')
                    FROM evaluations
                )
                ||
                (
                    SELECT ST_AsMVT(observations.*, %s, 4096, 'mvtgeom', 'uuid')
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
            + (f'sites-{evaluation_run_uuid}',
               f'observations-{evaluation_run_uuid}',
               f'regions-{evaluation_run_uuid}')
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
