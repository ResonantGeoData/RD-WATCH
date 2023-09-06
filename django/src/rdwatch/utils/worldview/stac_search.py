import json
from datetime import datetime, timedelta
import logging
from os import path
from typing import Literal, TypedDict
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


class EOBand(TypedDict):
    name: str


class Link(TypedDict):
    rel: str
    href: str


Asset = TypedDict(
    'Asset',
    {
        'eo:bands': list[EOBand],
        'href': str,
    },
)

Properties = TypedDict(
    'Properties',
    {
        'datetime': str,
        'mission': Literal['WV01', 'GE01', 'WV02', 'WV03', 'WV04'],
        'instruments': list[Literal['vis-multi', 'panchromatic', 'swir-multi']],
        'nitf:bits_per_pixel': int,
        'nitf:image_representation': Literal['MULTI', 'MONO', 'RGB'],
        'nitf:compression': Literal['C8', 'NC'],
    },
)


class Feature(TypedDict):
    id: str
    collection: str
    properties: Properties
    assets: dict[Literal['data'], Asset]
    bbox: list[float]


class Context(TypedDict):
    matched: int
    limit: int


class Results(TypedDict):
    context: Context
    features: list[Feature]
    links: list[Link]


class SearchParams(TypedDict, total=False):
    bbox: tuple[float, float, float, float]
    datetime: str
    collections: list[str]
    page: int
    limit: int

COLLECTIONS: list[str] = []

if settings.ACCENTURE_VERSION is not None:
    COLLECTIONS.append(f'ta1-wv-acc-{settings.ACCENTURE_VERSION}')


def _fmt_time(time: datetime):
    return f'{time.isoformat()[:19]}Z'


def worldview_search(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
    page: int = 1,
) -> Results:
    url = path.join(settings.SMART_STAC_URL, 'search')
    params = SearchParams()
    params['bbox'] = bbox
    if timebuffer is not None:
        min_time = timestamp - timebuffer
        max_time = timestamp + timebuffer
        time_str = f'{_fmt_time(min_time)}/{_fmt_time(max_time)}'
    else:
        time_str = f'{_fmt_time(timestamp)}Z'
    params['datetime'] = time_str
    params['collections'] = COLLECTIONS
    params['page'] = page
    params['limit'] = 100
    request = Request(
        url,
        data=bytes(json.dumps(params), 'utf-8'),
        headers={'x-api-key': settings.SMART_STAC_KEY},
    )
    logger.warning(request.full_url)
    logger.warning(params)
    with urlopen(request) as resp:
        read = resp.read()
        logger.warning(read)
        return json.loads(read)
