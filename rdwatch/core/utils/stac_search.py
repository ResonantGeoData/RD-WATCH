import logging
from datetime import datetime, timedelta
from typing import Literal, TypedDict, cast

from pystac_client import Client

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


COLLECTIONS: dict[str, list[str]] = {
    'L8': [],
    'S2': ['sentinel-2-c1-l2a', 'sentinel-2-l2a'],
    'PL': [],
}

STAC_URL = 'https://earth-search.aws.element84.com/v1/'


def stac_search(
    source: Literal['S2', 'L8', 'PL'],
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> Results:
    stac_catalog = Client.open(STAC_URL)

    if timebuffer is not None:
        min_time = timestamp - timebuffer
        max_time = timestamp + timebuffer
        time_str = f'{_fmt_time(min_time)}/{_fmt_time(max_time)}'
    else:
        time_str = f'{_fmt_time(timestamp)}Z'
    if source not in COLLECTIONS:
        logger.warning(
            'Source {source} not in Collections: {COLLECTIONS} returning empty list'
        )
        return {'features': [], 'links': []}
    results = stac_catalog.search(
        method='GET',
        bbox=bbox,
        datetime=time_str,
        collections=COLLECTIONS[source],
        limit=100,
    )
    # TODO: return `results` directly instead of converting to a dict.
    # Before that can happen, the callers need to be updated to handle
    # an `ItemSearch` object.
    return cast(Results, results.item_collection_as_dict())
