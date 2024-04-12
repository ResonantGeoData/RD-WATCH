from datetime import datetime, timedelta

from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Area, Transform
from django.core.cache import cache
from django.db import connections
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    ExpressionWrapper,
    F,
    Field,
    Func,
    IntegerField,
    Min,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
    Window
)
from django.db.models.functions import Cast, Concat, Lower, Replace, Substr
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from pydantic import UUID4

from rdwatch.db.functions import ExtractEpoch, GroupExcludeRowRange
from rdwatch_scoring.models import (
    AnnotationProposalObservation,
    AnnotationProposalSet,
    AnnotationProposalSite,
    EvaluationBroadAreaSearchDetection,
    EvaluationBroadAreaSearchProposal,
    EvaluationRun,
    Observation,
    Region,
    Site, AnnotationGroundTruthSite, AnnotationGroundTruthObservation,
)
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


def vector_tile_proposal(
    request: HttpRequest, annotation_proposal_set_uuid: UUID4, z: int, x: int, y: int
):
    annotation_proposal_set = get_object_or_404(AnnotationProposalSet, pk=annotation_proposal_set_uuid)

    latest_timestamp = annotation_proposal_set.create_datetime

    # Generate a unique cache key based on the model run ID, vector tile coordinates,
    # and the latest timestamp
    cache_key = _get_vector_tile_cache_key(
        annotation_proposal_set_uuid, z, x, y, latest_timestamp
    )

    tile = None

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

        geomfromtext = Func(
            'geometry', 4326, function='ST_GeomFromText', output_field=Field()
        )

        site_queryset = (
            AnnotationProposalSite.objects.filter(annotation_proposal_set_uuid=annotation_proposal_set_uuid)
            .alias(geomfromtext=geomfromtext)
            .alias(transformedgeom=transform)
            # .alias(base_site_id=F('site_id'))
            .filter(intersects)
            .values()
            .annotate(
                id=F('uuid'),
                mvtgeom=mvtgeom,
                configuration_id=F('annotation_proposal_set_uuid'),
                configuration_name=ExpressionWrapper(
                    Concat(
                        Value('Proposal '),
                        F('originator'),
                        Value(' '),
                        F('region_id')
                    ),
                    output_field=CharField(),
                ),
                label=Case(
                    When(
                        Q(status__isnull=False),
                        Lower(Replace('status', Value(' '), Value('_'))),
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
                color_code=Value(None, output_field=IntegerField()),
            )
            .values('site_id', 'region_id_id', 'mgrs', 'version', 'start_date', 'end_date', 'originator', 'status',
                    'validated', 'score', 'geometry', 'uuid', 'proposal_status', 'comments', 'id', 'mvtgeom',
                    'configuration_id', 'configuration_name', 'label', 'timestamp', 'timemin', 'timemax',
                    'performer_id', 'performer_name', 'region', 'groundtruth', 'site_polygon', 'site_number', 'color_code')
        )
        (
            site_sql,
            site_params,
        ) = site_queryset.query.sql_with_params()

        ground_truth_site_queryset = (
            AnnotationGroundTruthSite.objects.filter(region_id=site_queryset.values('region_id')[:1])
            .alias(geomfromtext=geomfromtext)
            .alias(transformedgeom=transform)
            .filter(intersects)
            .values()
            .annotate(
                id=F('uuid'),
                mvtgeom=mvtgeom,
                configuration_id=Value(annotation_proposal_set_uuid, output_field=CharField()),
                configuration_name=ExpressionWrapper(
                    Concat(
                        Value('GT '),
                        F('region_id')
                    ),
                    output_field=CharField(),
                ),
                label=Case(
                    When(
                        Q(status__isnull=False),
                        Lower(Replace('status', Value(' '), Value('_'))),
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
                groundtruth=Value(True),
                site_polygon=Value(False, output_field=BooleanField()),
                site_number=Substr(F('site_id'), 9),  # pos is 1 indexed
                color_code=Value(None, output_field=IntegerField()),
                proposal_status=Value(None, output_field=CharField()),
                comments=Value(None, output_field=CharField())
            )
            .values('site_id', 'region_id_id', 'mgrs', 'version', 'start_date', 'end_date', 'originator', 'status',
                    'validated', 'score', 'geometry', 'uuid', 'proposal_status', 'comments', 'id', 'mvtgeom',
                    'configuration_id', 'configuration_name', 'label', 'timestamp', 'timemin', 'timemax',
                    'performer_id', 'performer_name', 'region', 'groundtruth', 'site_polygon', 'site_number', 'color_code')
        )
        (
            ground_truth_site_sql,
            ground_truth_site_params,
        ) = ground_truth_site_queryset.query.sql_with_params()

        (
            site_union_sql,
            site_union_params,
        ) = site_queryset.union(ground_truth_site_queryset, all=True).query.sql_with_params()

        observations_queryset = (
            AnnotationProposalObservation.objects.filter(
                annotation_proposal_set_uuid=annotation_proposal_set_uuid
            )
            .alias(geomfromtext=geomfromtext)
            .alias(transformedgeom=transform)
            .filter(intersects)
            .values()
            .annotate(
                id=F('uuid'),
                timestamp=F('observation_date'),
                mvtgeom=mvtgeom,
                configuration_id=F('annotation_proposal_set_uuid'),
                configuration_name=ExpressionWrapper(
                    Concat(
                        Value('Proposal '),
                        F('annotation_proposal_site_uuid__originator'),
                        Value(' '),
                        F('annotation_proposal_site_uuid__region_id')
                    ),
                    output_field=CharField(),
                ),
                site_label=F('annotation_proposal_site_uuid__status'),
                site_number=Substr(F('annotation_proposal_site_uuid__site_id'), 9),  # pos is 1 indexed
                label=Cast("current_phase", output_field=CharField()),  # This should be an ID, on client side can make it understand this
                area=Area(Transform('transformedgeom', srid=6933)),
                siteeval_id=F('annotation_proposal_site_uuid'),
                timemin=ExtractEpoch('observation_date'),
                timemax=ExtractEpoch(
                    Window(
                        expression=Min('observation_date'),
                        partition_by=[F('annotation_proposal_site_uuid')],
                        frame=GroupExcludeRowRange(start=0, end=None),
                        order_by='observation_date',
                    ),
                ),  # This probably needs to be using the site tables start/end dates
                performer_id=F('annotation_proposal_site_uuid__originator'),
                performer_name=F('annotation_proposal_site_uuid__originator'),
                region=F('annotation_proposal_site_uuid__region_id'),
                version=F('annotation_proposal_site_uuid__version'),
                score=Cast("score", output_field=CharField()),
                groundtruth=Case(
                    When(
                        Q(annotation_proposal_site_uuid__originator='te')
                        | Q(annotation_proposal_site_uuid__originator='iMERIT'),
                        True,
                        ),
                    default=False,
                ),
            )
            .values('site_id', 'observation_date', 'source', 'sensor_name', 'score', 'current_phase', 'is_occluded',
                    'is_site_boundary', 'geometry', 'uuid', 'id', 'timestamp', 'mvtgeom', 'configuration_id',
                    'configuration_name', 'site_label', 'site_number', 'label', 'area', 'siteeval_id',
                    'timemin', 'timemax', 'performer_id', 'performer_name', 'region', 'version', 'groundtruth')
        )

        (
            observations_sql,
            observations_params,
        ) = observations_queryset.query.sql_with_params()

        ground_truth_observations_queryset = (
            AnnotationGroundTruthObservation.objects.filter(
                annotation_ground_truth_site_uuid__in=ground_truth_site_queryset.values_list('uuid', flat=True)
            )
            .alias(geomfromtext=geomfromtext)
            .alias(transformedgeom=transform)
            .filter(intersects)
            .values()
            .annotate(
                id=F('uuid'),
                timestamp=F('observation_date'),
                mvtgeom=mvtgeom,
                configuration_id=Value(annotation_proposal_set_uuid, output_field=CharField()),
                configuration_name=ExpressionWrapper(
                    Concat(
                        Value('GT '),
                        F('annotation_ground_truth_site_uuid__region_id')
                    ),
                    output_field=CharField(),
                ),
                site_label=F('annotation_ground_truth_site_uuid__status'),
                site_number=Substr(F('annotation_ground_truth_site_uuid__site_id'), 9),  # pos is 1 indexed
                label=Cast("current_phase", output_field=CharField()),  # This should be an ID, on client side can make it understand this
                area=Area(Transform('transformedgeom', srid=6933)),
                siteeval_id=F('annotation_ground_truth_site_uuid'),
                timemin=ExtractEpoch('observation_date'),
                timemax=ExtractEpoch(
                    Window(
                        expression=Min('observation_date'),
                        partition_by=[F('annotation_ground_truth_site_uuid')],
                        frame=GroupExcludeRowRange(start=0, end=None),
                        order_by='observation_date',
                    ),
                ),  # This probably needs to be using the site tables start/end dates
                performer_id=F('annotation_ground_truth_site_uuid__originator'),
                performer_name=F('annotation_ground_truth_site_uuid__originator'),
                region=F('annotation_ground_truth_site_uuid__region_id'),
                version=F('annotation_ground_truth_site_uuid__version'),
                score=Cast("score", output_field=CharField()),
                groundtruth=Value(True),
            )
            .values('site_id', 'observation_date', 'source', 'sensor_name', 'score', 'current_phase', 'is_occluded',
                    'is_site_boundary', 'geometry', 'uuid', 'id', 'timestamp', 'mvtgeom', 'configuration_id',
                    'configuration_name', 'site_label', 'site_number', 'label', 'area', 'siteeval_id',
                    'timemin', 'timemax', 'performer_id', 'performer_name', 'region', 'version', 'groundtruth')
        )
        (
            ground_truth_observations_sql,
            ground_truth_observations_params,
        ) = ground_truth_observations_queryset.query.sql_with_params()

        (
            observations_union_sql,
            observations_union_params,
        ) = observations_queryset.union(ground_truth_observations_queryset, all=True).query.sql_with_params()

        region_queryset = (
            Region.objects.filter(id=site_queryset.values('region_id')[:1])
            .alias(geomfromtext=geomfromtext)
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
                sites AS ({site_union_sql}),
                observations AS ({observations_union_sql}),
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
            site_union_params
            + observations_union_params
            + region_params
            + (
                f'sites-{annotation_proposal_set_uuid}',
                f'observations-{annotation_proposal_set_uuid}',
                f'regions-{annotation_proposal_set_uuid}',
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


@router.get('/{evaluation_run_uuid}/vector-tile/{z}/{x}/{y}.pbf/')
def vector_tile(
    request: HttpRequest, evaluation_run_uuid: UUID4, z: int, x: int, y: int
):
    proposal = True if request.GET.get('proposal') else False
    if proposal:
        return vector_tile_proposal(request, evaluation_run_uuid, z, x, y)

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
