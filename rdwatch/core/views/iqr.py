from collections import defaultdict
import json
import logging
import bisect
from typing import Literal

import requests
from ninja import Router, Schema

from django.core.files.storage import default_storage
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.core.models import SiteEvaluation, SiteImage, SiteObservation, lookups

logger = logging.getLogger(__name__)
router = Router()
session = requests.Session()

BASE = 'http://iqr_rest:5001'


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
    site_id: str
    image_url: str | None
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


def pick_site_image(images: list[SiteImage], observations: list[SiteObservation]) -> SiteImage | None:
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
    for smqtk_uuid, confidence in resp_results['results'][:50]:
        uuids.append(smqtk_uuid)
        confidence_by_uuid[smqtk_uuid] = confidence

    site_evals = SiteEvaluation.objects.filter(smqtk_uuid__in=uuids)
    site_ids = [site.id for site in site_evals]

    images_by_site = defaultdict(list)
    for site_image in SiteImage.objects.filter(site__in=site_ids).order_by('timestamp'):
        images_by_site[site_image.site.id].append(site_image)

    observations_by_site = defaultdict(list)
    for obs in SiteObservation.objects.filter(siteeval__in=site_ids).order_by('timestamp'):
        observations_by_site[obs.siteeval.id].append(obs)

    ordered_results = {
        'sid': sid,
        'total_results': resp_results['total_results'],
        'results': [],
    }
    for site in site_evals:
        site_image = pick_site_image(images_by_site[site.id], observations_by_site[site.id])
        image_url = default_storage.url(site_image.image.name) if site_image else None
        ordered_results['results'].append(
            {
                'pk': str(site.id),
                'site_id': str(site.site_id),
                'image_url': image_url,
                'smqtk_uuid': site.smqtk_uuid,
                'confidence': confidence_by_uuid[site.smqtk_uuid],
                'geom': str(site.geom),
                'geom_extent': site.geom.transform(4326, clone=True).extent,
            }
        )

    ordered_results['results'] = sorted(ordered_results['results'], key=lambda r: -r['confidence'])
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
    observations = list(SiteObservation.objects.filter(siteeval=site).order_by('timestamp'))
    images = list(SiteImage.objects.filter(site=site).order_by('timestamp'))
    site_image = pick_site_image(images, observations)
    return default_storage.url(site_image.image.name) if site_image else None
