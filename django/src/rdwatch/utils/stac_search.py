import json
from datetime import datetime, timedelta
from typing import List, Literal, Optional, Tuple, TypedDict
from urllib.request import urlopen


class EOBand(TypedDict, total=False):
    name: str
    common_name: str


class AlternateS3Link(TypedDict, total=False):
    href: str


Asset = TypedDict(
    "Asset",
    {
        "eo:bands": list[EOBand],
        "href": str,
        "alternate": dict[Literal["s3"], AlternateS3Link],
    },
    total=False,
)


class Properties(TypedDict, total=False):
    datetime: str


class Feature(TypedDict, total=False):
    collection: str
    properties: Properties
    assets: dict[str, Asset]
    bbox: List[float]


class Results(TypedDict, total=False):
    features: list[Feature]


class SearchParams(TypedDict, total=False):
    bbox: Tuple[float, float, float, float]
    datetime: str
    collections: List[str]


def _fmt_time(time: datetime):
    return f"{time.isoformat()[:19]}Z"


def landsat_search(
    timestamp: datetime,
    bbox: Tuple[float, float, float, float],
    timebuffer: Optional[timedelta] = None,
) -> Results:
    url = "https://landsatlook.usgs.gov/stac-server/search"
    if timebuffer is not None:
        min_time = timestamp - timebuffer
        max_time = timestamp + timebuffer
        time_str = f"?datetime={_fmt_time(min_time)}/{_fmt_time(max_time)}"
    else:
        time_str = f"?datetime={_fmt_time(timestamp)}"
    url += time_str
    url += f"&bbox={','.join(str(coord) for coord in bbox)}"
    url += "&collections=landsat-c2l1,landsat-c2l2-sr"
    with urlopen(url) as resp:
        return json.loads(resp.read())


def sentinel_search(
    timestamp: datetime,
    bbox: Tuple[float, float, float, float],
    timebuffer: Optional[timedelta] = None,
) -> Results:
    url = "https://earth-search.aws.element84.com/v0/search"
    params = SearchParams()
    params["bbox"] = bbox
    if timebuffer is not None:
        min_time = timestamp - timebuffer
        max_time = timestamp + timebuffer
        time_str = f"{_fmt_time(min_time)}/{_fmt_time(max_time)}"
    else:
        time_str = f"{_fmt_time(timestamp)}Z"
    params["datetime"] = time_str
    params["collections"] = [
        "sentinel-s2-l1c",
        "sentinel-s2-l2a",
        "sentinel-s2-l2a-cogs",
    ]
    with urlopen(url, bytes(json.dumps(params), "utf-8")) as resp:
        return json.loads(resp.read())
