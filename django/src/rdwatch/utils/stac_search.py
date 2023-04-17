import json
import logging
from datetime import datetime, timedelta
from os import environ, path
from typing import Literal, TypedDict
from urllib.request import Request, urlopen

from django.conf import settings
logger = logging.getLogger(__name__)


class EOBand(TypedDict, total=False):
    name: str
    common_name: str


class Link(TypedDict, total=False):
    rel: str
    href: str


Asset = TypedDict(
    'Asset',
    {
        'eo:bands': list[EOBand],
        'href': str,
        'alternate': dict[Literal['s3'], Link],
    },
    total=False,
)


class Properties(TypedDict, total=False):
    datetime: str


class Feature(TypedDict, total=False):
    collection: str
    properties: Properties
    assets: dict[str, Asset]
    bbox: list[float]


class Results(TypedDict, total=False):
    features: list[Feature]
    links: list[Link]


class SearchParams(TypedDict, total=False):
    bbox: tuple[float, float, float, float]
    datetime: str
    collections: list[str]
    page: int
    limit: int


def _fmt_time(time: datetime):
    return f'{time.isoformat()[:19]}Z'


COLLECTIONS: dict[str, list[str]] = {
    'L8': ['landsat-c2l1', 'landsat-c2l2-sr'],
    'S2': [],
}

if settings.ACCENTURE_IMAGERY_VERSION is not None:
    COLLECTIONS['S2'].append(f'ta1-s2-acc-{settings.ACCENTURE_IMAGERY_VERSION}')


def stac_search(
    source: Literal['S2', 'L8'],
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
    page: int = 1,
) -> Results:
    # Use SMART program server instead of public server
    # (https://earth-search.aws.element84.com/v0/search)
    url = path.join(environ['RDWATCH_SMART_STAC_URL'], 'search')
    params = SearchParams()
    params['bbox'] = bbox
    if timebuffer is not None:
        min_time = timestamp - timebuffer
        max_time = timestamp + timebuffer
        time_str = f'{_fmt_time(min_time)}/{_fmt_time(max_time)}'
    else:
        time_str = f'{_fmt_time(timestamp)}Z'
    params['datetime'] = time_str
    params['collections'] = COLLECTIONS[source]
    params['page'] = page
    params['limit'] = 100
    request = Request(
        url,
        data=bytes(json.dumps(params), 'utf-8'),
        headers={'x-api-key': environ['RDWATCH_SMART_STAC_KEY']},
    )
    logger.warning(request.get_full_url())
    logger.warning(f'Parms: {params}')
    with urlopen(request) as resp:
        return json.loads(resp.read())
