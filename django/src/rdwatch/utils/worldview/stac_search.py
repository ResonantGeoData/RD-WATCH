from datetime import datetime, timedelta
from typing import Literal, TypedDict, cast

from pystac_client import Client

from django.conf import settings


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


def _fmt_time(time: datetime):
    return f'{time.isoformat()[:19]}Z'


def worldview_search(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> Results:
    stac_catalog = Client.open(
        settings.SMART_STAC_URL,
        headers={'x-api-key': settings.SMART_STAC_KEY},
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
        collections=['worldview-nitf'],
        limit=100,
    )

    # TODO: return `results` directly instead of converting to a dict.
    # Before that can happen, the callers need to be updated to handle
    # an `ItemSearch` object.
    return cast(Results, results.item_collection_as_dict())
