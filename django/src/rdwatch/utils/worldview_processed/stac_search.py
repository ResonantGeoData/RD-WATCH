import logging
from datetime import datetime, timedelta
from typing import Literal, TypedDict, cast

from pystac_client import Client

from django.conf import settings

logger = logging.getLogger(__name__)


class Link(TypedDict):
    rel: str
    href: str


class Asset(TypedDict):
    href: str


Properties = TypedDict(
    'Properties',
    {
        'datetime': str,
        'nitf:image_representation': Literal['MULTI', 'MONO'],
    },
)


class Feature(TypedDict):
    id: str
    properties: Properties
    assets: dict[str, Asset]
    bbox: list[float]


class Context(TypedDict):
    matched: int
    limit: int


class Results(TypedDict):
    context: Context
    features: list[Feature]
    links: list[Link]


COLLECTIONS: list[str] = []

if settings.ACCENTURE_VERSION is not None:
    COLLECTIONS.append(f'ta1-wv-acc-{settings.ACCENTURE_VERSION}')


def _fmt_time(time: datetime):
    return f'{time.isoformat()[:19]}Z'

def request_modifier(x):
    print('ww processed here')
    print(x)

def worldview_search(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> Results:
    stac_catalog = Client.open(
        settings.SMART_STAC_URL,
        headers={'x-api-key': settings.SMART_STAC_KEY},
        request_modifier=request_modifier
    )

    if timebuffer is not None:
        min_time = timestamp - timebuffer
        max_time = timestamp + timebuffer
        time_str = f'{_fmt_time(min_time)}/{_fmt_time(max_time)}'
    else:
        time_str = f'{_fmt_time(timestamp)}Z'

    results = stac_catalog.search(
        method='GET',
        bbox=bbox,
        datetime=time_str,
        collections=COLLECTIONS,
        limit=100,
    )

    # TODO: return `results` directly instead of converting to a dict.
    # Before that can happen, the callers need to be updated to handle
    # an `ItemSearch` object.
    return cast(Results, results.item_collection_as_dict())
