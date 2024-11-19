import json
import logging
from typing import Literal

import requests
from ninja import Router, Schema

from django.core.files.storage import default_storage
from django.db.models import Case, When
from django.http import HttpRequest

from rdwatch.core.models import SiteEvaluation, SiteImage

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


@router.get('/{sid}/results', response={200: IQROrderedResults, 400: SuccessResponse})
def get_ordered_results(request: HttpRequest, sid: str):
    resp = session.get(f'{BASE}/get_results', params={'sid': sid})
    if resp.status_code != 200:
        logger.error('Could not get session info (code: %d)', resp.status_code)
        return 400, {'success': False}
    resp_results = resp.json()
    uuids: list[str] = []
    for smqtk_uuid, _ in resp_results['results'][:50]:
        uuids.append(smqtk_uuid)

    order_by = Case(
        *[When(smqtk_uuid=uuid, then=pos) for pos, uuid in enumerate(uuids)]
    )
    site_evals = SiteEvaluation.objects.filter(smqtk_uuid__in=uuids).order_by(order_by)

    # TODO maybe use distinct on + left join
    # select distinct on (site_image.site_eval_id) * from ...

    site_eval_ids = [site_eval.id for site_eval in site_evals]
    image_by_site_id = {
        image.site.id: image
        for image in SiteImage.objects.filter(site__in=site_eval_ids)
    }

    rich_results = {
        'sid': sid,
        'total_results': resp_results['total_results'],
        'results': [],
    }
    for site_eval, result_item in zip(site_evals, resp_results['results']):
        smqtk_uuid, confidence = result_item
        assert site_eval.smqtk_uuid == smqtk_uuid, 'Mismatching smqtk uuids'

        site_image = image_by_site_id.get(site_eval.id, None)
        site_image_url = default_storage.url(site_image.image.name) if site_image else None

        rich_results['results'].append(
            {
                'pk': str(site_eval.id),
                'site_id': str(site_eval.site_id),
                'image_url': site_image_url,
                'smqtk_uuid': smqtk_uuid,
                'confidence': confidence,
                'geom': str(site_eval.geom),
            }
        )

    return 200, rich_results


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
