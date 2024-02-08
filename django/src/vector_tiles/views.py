from datetime import datetime, timedelta
from typing import Literal

from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Area, Transform
from django.core.cache import cache
from django.db import connection, connections
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    ExpressionWrapper,
    F,
    Field,
    Func,
    Max,
    Min,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
    Window,
)
from django.db.models.functions import Concat, Lower, Replace, Substr
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404


def _get_vector_tile_cache_key(
    model_run_id: str, z: int, x: int, y: int, timestamp: datetime
) -> str:
    from rdwatch.models import ModelRun

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


def rgd_vector_tiles(request: HttpRequest, model_run_id: str, z: int, x: int, y: int):
    from rdwatch.db.functions import ExtractEpoch, GroupExcludeRowRange
    from rdwatch.models import ModelRun, Region, SiteEvaluation, SiteObservation

    timestamps: dict[
        Literal[
            'latest_evaluation_timestamp',
            'model_run_timestamp',
        ],
        datetime | None,
    ] = ModelRun.objects.filter(id=model_run_id).aggregate(
        # Get timestamp of most recent site evaluation so we can use it as a cache key
        latest_evaluation_timestamp=Max('evaluations__modified_timestamp'),
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
                uuid=F(
                    'pk'
                ),  # maintain consistency with scoring DB for clicking on items
                mvtgeom=mvtgeom,
                configuration_id=F('configuration_id'),
                configuration_name=F('configuration__title'),
                label=F('label__slug'),
                timestamp=ExtractEpoch('timestamp'),
                timemin=ExtractEpoch('start_date'),
                timemax=ExtractEpoch('end_date'),
                performer_id=F('configuration__performer_id'),
                performer_name=F('configuration__performer__slug'),
                region=F('region__name'),
                groundtruth=Case(
                    When(
                        Q(configuration__performer__slug='TE') & Q(score=1),
                        True,
                    ),
                    default=False,
                ),
                site_number=F('number'),
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
                configuration_name=F('siteeval__configuration__title'),
                site_label=F('siteeval__label__slug'),
                site_number=F('siteeval__number'),
                label=F('label__slug'),
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
                performer_name=F('siteeval__configuration__performer__slug'),
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
                    SELECT ST_AsMVT(evaluations.*, %s, 4096, 'mvtgeom')
                    FROM evaluations
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


def _get_scoring_vector_tile_cache_key(
    evaluation_run_uuid: str, z: int, x: int, y: int, timestamp: datetime
) -> str:
    from rdwatch_scoring.models import Site

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


def rgd_scoring_vector_tiles(
    request: HttpRequest, evaluation_run_uuid: str, z: int, x: int, y: int
):
    from rdwatch.db.functions import ExtractEpoch, GroupExcludeRowRange
    from rdwatch_scoring.models import (
        EvaluationBroadAreaSearchDetection,
        EvaluationBroadAreaSearchProposal,
        EvaluationRun,
        Observation,
        Region,
        Site,
    )

    evaluation_run = get_object_or_404(EvaluationRun, pk=evaluation_run_uuid)

    latest_timestamp = evaluation_run.start_datetime

    # Generate a unique cache key based on the model run ID, vector tile coordinates,
    # and the latest timestamp
    cache_key = _get_scoring_vector_tile_cache_key(
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
            .alias(base_site_id=F('site_id'))
            .filter(intersects)
            .values()
            .annotate(
                id=F('base_site_id'),
                mvtgeom=mvtgeom,
                configuration_id=F('evaluation_run_uuid'),
                configuration_name=ExpressionWrapper(
                    Concat(
                        Value('Eval '),
                        F('evaluation_run_uuid__evaluation_number'),
                        Value(' '),
                        F('evaluation_run_uuid__evaluation_run_number'),
                        Value(' '),
                        F('evaluation_run_uuid__performer'),
                    ),
                    output_field=CharField(),
                ),
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
                performer_name=F('originator'),
                region=F('region_id'),
                groundtruth=Case(
                    When(
                        Q(originator='te') | Q(originator='iMERIT'),
                        True,
                    ),
                    default=False,
                ),
                site_polygon=Value(False, output_field=BooleanField()),
                site_number=Substr(F('site_id'), 9),  # pos is 1 indexed
                color_code=Case(
                    When(
                        Q(originator='te') | Q(originator='iMERIT'),
                        then=Subquery(
                            EvaluationBroadAreaSearchDetection.objects.filter(
                                evaluation_run_uuid=evaluation_run_uuid,
                                activity_type='overall',
                                rho=0.5,
                                tau=0.2,
                                min_confidence_score=0.0,
                                site_truth=OuterRef('base_site_id'),
                            ).values('color_code')
                        ),
                    ),
                    When(
                        ~Q(originator='te') & ~Q(originator='iMERIT'),
                        then=Subquery(
                            EvaluationBroadAreaSearchProposal.objects.filter(
                                evaluation_run_uuid=evaluation_run_uuid,
                                activity_type='overall',
                                rho=0.5,
                                tau=0.2,
                                min_confidence_score=0.0,
                                site_proposal=OuterRef('base_site_id'),
                            ).values('color_code')
                        ),
                    ),
                    default=Value(None),  # Set an appropriate default value here
                ),
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
                configuration_name=ExpressionWrapper(
                    Concat(
                        Value('Eval '),
                        F('site_uuid__evaluation_run_uuid__evaluation_number'),
                        Value(' '),
                        F('site_uuid__evaluation_run_uuid__evaluation_run_number'),
                        Value(' '),
                        F('site_uuid__evaluation_run_uuid__performer'),
                    ),
                    output_field=CharField(),
                ),
                site_label=F('site_uuid__status_annotated'),
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
                performer_name=F('site_uuid__originator'),
                region=F('site_uuid__region_id'),
                version=F('site_uuid__version'),
                score=F('confidence_score'),
                groundtruth=Case(
                    When(
                        Q(site_uuid_id__originator='te')
                        | Q(site_uuid_id__originator='iMERIT'),
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
