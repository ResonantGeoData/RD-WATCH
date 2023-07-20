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
from django.http import HttpRequest, HttpResponse

from rdwatch.db.functions import ExtractEpoch, GroupExcludeRowRange
from rdwatch.models import Region, SiteEvaluation, SiteObservation

from .model_run import router


@router.get('/{hyper_parameters_id}/vector-tile/{z}/{x}/{y}.pbf/')
def vector_tile(request: HttpRequest, hyper_parameters_id: int, z: int, x: int, y: int):
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
        SiteEvaluation.objects.filter(configuration_id=hyper_parameters_id)
        .filter(intersects)
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
        SiteObservation.objects.filter(siteeval__configuration_id=hyper_parameters_id)
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
        Region.objects.filter(evaluations__configuration_id=hyper_parameters_id)
        .filter(intersects)
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
                SELECT ST_AsMVT(evaluations.*, 'sites-%s', 4096, 'mvtgeom', 'id')
                FROM evaluations
            )
            ||
            (
                SELECT ST_AsMVT(observations.*, 'observations-%s', 4096, 'mvtgeom', 'id')
                FROM observations
            )
            ||
            (
                SELECT ST_AsMVT(regions.*, 'regions-%s', 4096, 'mvtgeom', 'id')
                FROM regions
            )
        )
    """  # noqa: E501
    params = (
        evaluations_params
        + observations_params
        + regions_params
        + (hyper_parameters_id,) * 3
    )

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    tile = row[0]

    return HttpResponse(
        tile,
        content_type='application/octet-stream',
        status=200 if tile else 204,
    )
