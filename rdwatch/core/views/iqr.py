import bisect
import json
import logging
from collections import defaultdict
from typing import Literal

import requests
from ninja import Router, Schema

from django.contrib.gis.db.models.functions import Area, Transform
from django.core.files.storage import default_storage
from django.db import connection
from django.db.models import (
    BooleanField,
    Case,
    Count,
    F,
    Field,
    Func,
    Min,
    Q,
    When,
    Window,
)
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.core.db.functions import ExtractEpoch, GroupExcludeRowRange
from rdwatch.core.models import SiteEvaluation, SiteImage, SiteObservation

logger = logging.getLogger(__name__)
router = Router()
session = requests.Session()

BASE = 'http://iqr_rest:5001'
MAX_RESULTS = 50


class SuccessResponse(Schema):
    success: bool


class IQRInitializeRequest(Schema):
    sid: str | None
    init_pos_uuid: str


class IQRInitializeResponse(SuccessResponse):
    sid: str | None


class IQRSessionInfo(Schema):
    sid: str
    time: dict
    uuids_neg: list[str]
    uuids_neg_ext: list[str]
    uuids_neg_ext_in_model: list[str]
    uuids_neg_in_model: list[str]
    uuids_pos: list[str]
    uuids_pos_ext: list[str]
    uuids_pos_ext_in_model: list[str]
    uuids_pos_in_model: list[str]
    wi_count: int


class IQROrderedResultItem(Schema):
    pk: str
    site_uid: str
    site_id: str
    image_url: str | None
    image_bbox: tuple[float, float, float, float] | None
    smqtk_uuid: str
    confidence: float
    geom: str
    geom_extent: list[float]


class IQROrderedResults(Schema):
    sid: str
    # i: int
    # j: int
    total_results: int
    results: list[IQROrderedResultItem]
    # results: list[tuple[str, float]]


class IQRAdjudicationEntry(Schema):
    uuid: str
    status: Literal['positive', 'neutral', 'negative']


class IQRAdjudicationRequest(Schema):
    adjudications: list[IQRAdjudicationEntry]


@router.post('/initialize', response={200: IQRInitializeResponse, 400: SuccessResponse})
def initialize(request: HttpRequest, init_data: IQRInitializeRequest):
    sid = init_data.sid
    if not sid:
        resp = session.post(f'{BASE}/session')
        if resp.status_code != 201:
            logger.error('Could not create session (code: %d)', resp.status_code)
            return 400, {'success': False}
        sid = resp.json()['sid']

    resp = session.put(f'{BASE}/session', data={'sid': sid})
    if resp.status_code != 200:
        logger.error('Could not initialize session (code: %d)', resp.status_code)
        return 400, {'success': False}

    resp = session.post(
        f'{BASE}/adjudicate',
        data={
            'sid': sid,
            'pos': json.dumps([init_data.init_pos_uuid]),
            'neg': json.dumps([]),
            'neutral': json.dumps([]),
        },
    )
    if resp.status_code != 200:
        logger.error('Could not adjudicate (code: %d)', resp.status_code)
        return 400, {'success': False}

    resp = session.post(f'{BASE}/initialize', data={'sid': sid})
    resp.raise_for_status()
    data = resp.json()
    return 200, {
        'sid': sid,
        'success': data.get('success', False),
    }


@router.post('/{sid}/refine', response={200: SuccessResponse, 400: SuccessResponse})
def refine(request: HttpRequest, sid: str):
    resp = session.post(f'{BASE}/refine', data={'sid': sid})
    if resp.status_code != 201:
        logger.error('Could not refine session (code: %d)', resp.status_code)
        return 400, {'success': False}
    return 200, {'success': True}


@router.get('/{sid}', response={200: IQRSessionInfo, 400: SuccessResponse})
def get_session_info(request: HttpRequest, sid: str):
    resp = session.get(f'{BASE}/session', params={'sid': sid})
    if resp.status_code != 200:
        logger.error('Could not get session info (code: %d)', resp.status_code)
        return 400, {'success': False}
    return 200, resp.json()


def pick_site_image(
    images: list[SiteImage], observations: list[SiteObservation]
) -> SiteImage | None:
    # ignore observations with no timestamps
    observations = [o for o in observations if o.timestamp is not None]

    if not len(images):
        return None
    if not len(observations):
        return images[-1]

    # pick either last active_construction observation, or first post_construction observation
    # if no active_construction or post_construction, pick last observation
    obs_candidate = observations[-1]
    for obs in observations[::-1]:
        if obs.label.slug == 'active_construction':
            obs_candidate = obs
            break
        if obs.label.slug == 'post_construction':
            obs_candidate = obs

    # find image closest to obs_candidate.timestamp
    idx = bisect.bisect_left(images, obs_candidate.timestamp, key=lambda v: v.timestamp)
    if idx == len(images):
        return images[-1]
    return images[idx]


@router.get('/{sid}/results', response={200: IQROrderedResults, 400: SuccessResponse})
def get_ordered_results(request: HttpRequest, sid: str):
    resp = session.get(f'{BASE}/get_results', params={'sid': sid})
    if resp.status_code != 200:
        logger.error('Could not get session info (code: %d)', resp.status_code)
        return 400, {'success': False}
    resp_results = resp.json()
    uuids: list[str] = []
    confidence_by_uuid = {}
    for smqtk_uuid, confidence in resp_results['results']:
        uuids.append(smqtk_uuid)
        confidence_by_uuid[smqtk_uuid] = confidence

    site_evals = SiteEvaluation.objects.filter(smqtk_uuid__in=uuids)
    site_evals = sorted(
        [site for site in site_evals],
        key=lambda site: -confidence_by_uuid[site.smqtk_uuid],
    )[:MAX_RESULTS]
    site_ids = [site.id for site in site_evals]

    images_by_site = defaultdict(list)
    for site_image in SiteImage.objects.filter(site__in=site_ids).order_by('timestamp'):
        images_by_site[site_image.site.id].append(site_image)

    observations_by_site = defaultdict(list)
    for obs in SiteObservation.objects.filter(siteeval__in=site_ids).order_by(
        'timestamp'
    ):
        observations_by_site[obs.siteeval.id].append(obs)

    ordered_results = {
        'sid': sid,
        'total_results': resp_results['total_results'],
        'results': [],
    }
    for site in site_evals:
        site_image = pick_site_image(
            images_by_site[site.id], observations_by_site[site.id]
        )
        image_url = default_storage.url(site_image.image.name) if site_image else None
        image_bbox = (
            site_image.image_bbox.extent
            if site_image and site_image.image_bbox
            else None
        )
        ordered_results['results'].append(
            {
                'pk': str(site.id),
                'site_uid': str(site.id),
                'site_id': str(site.site_id),
                'image_url': image_url,
                'image_bbox': image_bbox,
                'smqtk_uuid': site.smqtk_uuid,
                'confidence': confidence_by_uuid[site.smqtk_uuid],
                'geom': str(site.geom),
                'geom_extent': site.geom.transform(4326, clone=True).extent,
            }
        )

    ordered_results['results'] = sorted(
        ordered_results['results'], key=lambda r: -r['confidence']
    )
    return 200, ordered_results


@router.post('/{sid}/adjudicate', response={200: SuccessResponse, 400: SuccessResponse})
def adjudicate(request: HttpRequest, sid: str, adjudications: IQRAdjudicationRequest):
    positives: list[str] = []
    neturals: list[str] = []
    negatives: list[str] = []

    for entry in adjudications.adjudications:
        if entry.status == 'positive':
            positives.append(entry.uuid)
        elif entry.status == 'neutral':
            neturals.append(entry.uuid)
        elif entry.status == 'negative':
            negatives.append(entry.uuid)

    resp = session.post(
        f'{BASE}/adjudicate',
        data={
            'sid': sid,
            'pos': json.dumps(positives),
            'neg': json.dumps(negatives),
            'neutral': json.dumps(neturals),
        },
    )
    if resp.status_code != 200:
        logger.error('Could not adjudicate (code: %d)', resp.status_code)
        return 400, {'success': False}
    return 200, {'success': True}


@router.get('/site-image-url/{site_id}')
def get_site_image_url(request: HttpRequest, site_id: str):
    site = get_object_or_404(SiteEvaluation, id=site_id)
    observations = list(
        SiteObservation.objects.filter(siteeval=site).order_by('timestamp')
    )
    images = list(
        SiteImage.objects.filter(site=site, source='WV').order_by('timestamp')
    )
    site_image = pick_site_image(images, observations)
    return default_storage.url(site_image.image.name) if site_image else None


@router.get('/{sid}/vector-tile/{z}/{x}/{y}.pbf/')
def iqr_vector_tile(request: HttpRequest, sid: str, z: int, x: int, y: int):
    resp = session.get(f'{BASE}/get_results', params={'sid': sid})
    if resp.status_code != 200:
        logger.error('Could not get session info (code: %d)', resp.status_code)
        return HttpResponse('Bad Request', status=400)
    resp_results = resp.json()
    uuids: list[str] = []
    for smqtk_uuid, _ in resp_results['results'][:MAX_RESULTS]:
        uuids.append(smqtk_uuid)

    site_evals = SiteEvaluation.objects.filter(smqtk_uuid__in=uuids)
    site_ids = [site.id for site in site_evals]

    envelope = Func(z, x, y, function='ST_TileEnvelope')
    intersects_geom = Q(
        Func(
            'geom',
            envelope,
            function='ST_Intersects',
            output_field=BooleanField(),
        )
    )
    intersects_point = Q(
        Func(
            'point',
            envelope,
            function='ST_Intersects',
            output_field=BooleanField(),
        )
    )
    intersects = intersects_point | intersects_geom
    mvtgeom_point = Func(
        'point',
        envelope,
        function='ST_AsMVTGeom',
        output_field=Field(),
    )
    mvtgeom = Func(
        'geom',
        envelope,
        function='ST_AsMVTGeom',
        output_field=Field(),
    )

    evaluations_queryset = (
        SiteEvaluation.objects.filter(id__in=site_ids)
        .filter(intersects_geom)
        .values()
        .alias(observation_count=Count('observations'))
        .annotate(
            id=F('pk'),
            uuid=F('pk'),  # maintain consistency with scoring DB for clicking on items
            mvtgeom=mvtgeom,
            configuration_id=F('configuration_id'),
            configuration_name=F('configuration__title'),
            label=F('label__slug'),
            timestamp=ExtractEpoch('timestamp'),
            timemin=ExtractEpoch('start_date'),
            timemax=ExtractEpoch('end_date'),
            performer_id=F('configuration__performer_id'),
            performer_name=F('configuration__performer__short_code'),
            region=F('configuration__region__name'),
            groundtruth=Case(
                When(
                    Q(configuration__performer__short_code='TE') & Q(score=1),
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

    evaluations_points_queryset = (
        SiteEvaluation.objects.filter(id__in=site_ids)
        .filter(intersects_point)
        .values()
        .alias(observation_count=Count('observations'))
        .annotate(
            id=F('pk'),
            uuid=F('pk'),  # maintain consistency with scoring DB for clicking on items
            mvtgeom=mvtgeom_point,
            configuration_id=F('configuration_id'),
            configuration_name=F('configuration__title'),
            label=F('label__slug'),
            timestamp=ExtractEpoch('timestamp'),
            timemin=ExtractEpoch('start_date'),
            timemax=ExtractEpoch('end_date'),
            performer_id=F('configuration__performer_id'),
            performer_name=F('configuration__performer__short_code'),
            region=F('configuration__region__name'),
            groundtruth=Case(
                When(
                    Q(configuration__performer__short_code='TE') & Q(score=1),
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
        evaluations_points_sql,
        evaluations_points_params,
    ) = evaluations_points_queryset.query.sql_with_params()

    observations_queryset = (
        SiteObservation.objects.filter(siteeval__in=site_ids)
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
            performer_name=F('siteeval__configuration__performer__short_code'),
            region=F('siteeval__configuration__region__name'),
            version=F('siteeval__version'),
            groundtruth=Case(
                When(
                    Q(siteeval__configuration__performer__short_code='TE')
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

    observations_points_queryset = (
        SiteObservation.objects.filter(siteeval__in=site_ids)
        .filter(intersects_point)
        .values()
        .annotate(
            id=F('pk'),
            mvtgeom=mvtgeom_point,
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
            performer_name=F('siteeval__configuration__performer__short_code'),
            region=F('siteeval__configuration__region__name'),
            version=F('siteeval__version'),
            groundtruth=Case(
                When(
                    Q(siteeval__configuration__performer__short_code='TE')
                    & Q(siteeval__score=1),
                    True,
                ),
                default=False,
            ),
        )
    )
    (
        observations_points_sql,
        observations_points_params,
    ) = observations_points_queryset.query.sql_with_params()

    sql = f"""
        WITH
            evaluations AS ({evaluations_sql}),
            observations AS ({observations_sql}),
            evaluations_points AS ({evaluations_points_sql}),
            observations_points AS ({observations_points_sql})
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
                SELECT ST_AsMVT(evaluations_points.*, %s, 4096, 'mvtgeom')
                FROM evaluations_points
            )
            ||
            (
                SELECT ST_AsMVT(observations_points.*, %s, 4096, 'mvtgeom')
                FROM observations_points
            )
        )
    """  # noqa: E501
    params = (
        evaluations_params
        + observations_params
        + evaluations_points_params
        + observations_points_params
        + (
            f'sites-{sid}',
            f'observations-{sid}',
            f'sites_points-{sid}',
            f'observations_points-{sid}',
        )
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
