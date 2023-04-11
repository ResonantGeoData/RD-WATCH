import json
from datetime import datetime, timedelta
from os import environ, path
from typing import Literal, TypedDict
from urllib.request import Request, urlopen


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


def landsat_search(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
    page: int = 1,
) -> Results:
    url = 'https://landsatlook.usgs.gov/stac-server/search'
    if timebuffer is not None:
        min_time = timestamp - timebuffer
        max_time = timestamp + timebuffer
        time_str = f'?datetime={_fmt_time(min_time)}/{_fmt_time(max_time)}'
    else:
        time_str = f'?datetime={_fmt_time(timestamp)}'
    url += time_str
    url += f"&bbox={','.join(str(coord) for coord in bbox)}"
    url += '&collections=landsat-c2l1,landsat-c2l2-sr'
    url += f'&page={page}'
    url += '&limit=100'
    with urlopen(url) as resp:
        return json.loads(resp.read())


def sentinel_search(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
    page: int = 1,
) -> Results:
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
    params['collections'] = ['ta1-s2-acc-2']
    params['page'] = page
    params['limit'] = 100
    request = Request(
        url,
        data=bytes(json.dumps(params), 'utf-8'),
        headers={'x-api-key': environ['RDWATCH_SMART_STAC_KEY']},
    )
    with urlopen(request) as resp:
        return json.loads(resp.read())
