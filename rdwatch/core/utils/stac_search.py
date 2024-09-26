import logging
from datetime import datetime, timedelta
from itertools import chain
from typing import Literal, TypedDict

from pystac_client import Client, ItemSearch

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


def _fmt_time(time: datetime):
    return f'{time.isoformat()[:19]}Z'


COLLECTIONS_BY_SOURCE: dict[str, list[str]] = {
    'L8': ['landsat-c2l2-sr'],
    'S2': ['sentinel-2-c1-l2a', 'sentinel-2-l2a'],
    'PL': [],
}

SOURCES: list[str] = list(COLLECTIONS_BY_SOURCE.keys())
COLLECTIONS: list[str] = list(chain(*COLLECTIONS_BY_SOURCE.values()))

STAC_URLS: dict[str, str] = {
    'L8': 'https://landsatlook.usgs.gov/stac-server/',
    'S2': 'https://earth-search.aws.element84.com/v1/',
}


def stac_search(
    source: Literal['S2', 'L8', 'PL'],
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> ItemSearch:
    stac_catalog = Client.open(STAC_URLS[source])

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
        collections=COLLECTIONS_BY_SOURCE[source],
        limit=100,
    )

    return results
