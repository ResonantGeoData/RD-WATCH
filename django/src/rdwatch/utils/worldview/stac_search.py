import json
from datetime import datetime, timedelta
from os import environ, path
from typing import List, Literal, Optional, Tuple, TypedDict
from urllib.request import Request, urlopen


class EOBand(TypedDict):
    name: str


class Link(TypedDict):
    rel: str
    href: str


Asset = TypedDict(
    "Asset",
    {
        "eo:bands": list[EOBand],
        "href": str,
    },
)

Properties = TypedDict(
    "Properties",
    {
        "datetime": str,
        "mission": Literal["WV01", "GE01", "WV02", "WV03", "WV04"],
        "instruments": list[Literal["vis-multi", "panchromatic", "swir-multi"]],
        "nitf:bits_per_pixel": int,
        "nitf:image_representation": Literal["MULTI", "MONO", "RGB"],
    },
)


class Feature(TypedDict):
    id: str
    collection: str
    properties: Properties
    assets: dict[Literal["data"], Asset]
    bbox: List[float]


class Context(TypedDict):
    matched: int
    limit: int


class Results(TypedDict):
    context: Context
    features: list[Feature]
    links: list[Link]


class SearchParams(TypedDict, total=False):
    bbox: Tuple[float, float, float, float]
    datetime: str
    collections: List[str]
    page: int
    limit: int


def _fmt_time(time: datetime):
    return f"{time.isoformat()[:19]}Z"


def worldview_search(
    timestamp: datetime,
    bbox: Tuple[float, float, float, float],
    timebuffer: Optional[timedelta] = None,
    page: int = 1,
) -> Results:
    url = path.join(environ["RDWATCH_SMART_STAC_URL"], "search")
    params = SearchParams()
    params["bbox"] = bbox
    if timebuffer is not None:
        min_time = timestamp - timebuffer
        max_time = timestamp + timebuffer
        time_str = f"{_fmt_time(min_time)}/{_fmt_time(max_time)}"
    else:
        time_str = f"{_fmt_time(timestamp)}Z"
    params["datetime"] = time_str
    params["collections"] = ["worldview-nitf"]
    params["page"] = page
    params["limit"] = 100
    request = Request(
        url,
        data=bytes(json.dumps(params), "utf-8"),
        headers={"x-api-key": environ["RDWATCH_SMART_STAC_KEY"]},
    )
    with urlopen(request) as resp:
        return json.loads(resp.read())
