import json
import logging

from ninja import Router, Schema
from django.http import HttpRequest
import requests

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

class IQROrderedResults(Schema):
    sid: str
    i: int
    j: int
    total_results: int
    results: list[tuple[str, float]]

@router.post(
    '/initialize',
    response={200: IQRInitializeResponse, 400: SuccessResponse}
)
def initialize(request: HttpRequest, init_data: IQRInitializeRequest):
    sid = init_data.sid
    if not sid:
        resp = session.post(f'{BASE}/session')
        if resp.status_code != 201:
            logger.error('Could not create session (code: %d)', resp.status_code)
            return 400, { 'success': False }
        sid = resp.json()['sid']

    resp = session.put(f'{BASE}/session', data={'sid': sid})
    if resp.status_code != 200:
        logger.error('Could not initialize session (code: %d)', resp.status_code)
        return 400, { 'success': False }

    resp = session.post(f'{BASE}/adjudicate', data={
        'sid': sid,
        'pos': json.dumps([init_data.init_pos_uuid]),
        'neg': json.dumps([]),
        'neutral': json.dumps([]),
    })
    if resp.status_code != 200:
        logger.error('Could not adjudicate (code: %d)', resp.status_code)
        return 400, { 'success': False }

    resp = session.post(f'{BASE}/initialize', data={'sid': sid})
    resp.raise_for_status()
    data = resp.json()
    return 200, {
        'sid': sid,
        'success': data.get('success', False),
    }

@router.post(
    '/{sid}/refine',
    response={200: SuccessResponse, 400: SuccessResponse }
)
def refine(request: HttpRequest, sid: str):
    resp = session.post(f'{BASE}/refine', data={'sid': sid})
    if resp.status_code != 201:
        logger.error('Could not refine session (code: %d)', resp.status_code)
        return 400, { 'success': False }
    return 200, { 'success': True }

@router.get('/{sid}', response={200: IQRSessionInfo, 400: SuccessResponse})
def get_session_info(request: HttpRequest, sid: str):
    resp = session.get(f'{BASE}/session', params={'sid': sid})
    if resp.status_code != 200:
        logger.error('Could not get session info (code: %d)', resp.status_code)
        return 400, { 'success': False }
    return 200, resp.json()

@router.get('/{sid}/results', response={200: IQROrderedResults, 400: SuccessResponse})
def get_session_info(request: HttpRequest, sid: str):
    resp = session.get(f'{BASE}/get_results', params={'sid': sid})
    if resp.status_code != 200:
        logger.error('Could not get session info (code: %d)', resp.status_code)
        return 400, { 'success': False }
    return 200, resp.json()
