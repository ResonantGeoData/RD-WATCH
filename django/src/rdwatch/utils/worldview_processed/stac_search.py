import json
from datetime import datetime, timedelta
from os import environ, path
from typing import Literal, TypedDict
from urllib.request import Request, urlopen


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


class SearchParams(TypedDict, total=False):
    bbox: tuple[float, float, float, float]
    datetime: str
    collections: list[str]
    page: int
    limit: int


def _fmt_time(time: datetime):
    return f'{time.isoformat()[:19]}Z'


def worldview_search(
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
    params['collections'] = ['ta1-wv-acc-2']
    params['page'] = page
    params['limit'] = 100
    request = Request(
        url,
        data=bytes(json.dumps(params), 'utf-8'),
        headers={'x-api-key': environ['RDWATCH_SMART_STAC_KEY']},
    )
    with urlopen(request) as resp:
        data = resp.read()
        return json.loads(data)
