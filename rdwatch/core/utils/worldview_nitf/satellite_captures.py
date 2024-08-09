from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from rdwatch.core.utils.worldview_nitf.stac_search import worldview_search


@dataclass()
class WorldViewNITFCapture:
    timestamp: datetime
    bbox: tuple[float, float, float, float]
    uri: str
    cloudcover: int | None
    collection: str
    bits_per_pixel: int
    epsg: int


def get_features(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta,
):
    results = worldview_search(timestamp, bbox, timebuffer=timebuffer)
    yield from results['features']


def get_captures(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> list[WorldViewNITFCapture]:
    if timebuffer is None:
        timebuffer = timedelta(hours=1)

    features = [f for f in get_features(timestamp, bbox, timebuffer=timebuffer)]
    captures = []
    for feature in features:
        if 'data' in feature['assets']:
            cloudcover = 0
            if 'properties' in feature:
                if 'eo:cloud_cover' in feature['properties']:
                    cloudcover = feature['properties']['eo:cloud_cover']
            capture = WorldViewNITFCapture(
                timestamp=datetime.fromisoformat(
                    feature['properties']['datetime'].rstrip('Z')
                ),
                bbox=cast(tuple[float, float, float, float], tuple(feature['bbox'])),
                uri=feature['assets']['data']['href'],
                bits_per_pixel=feature['properties']['nitf:bits_per_pixel'],
                cloudcover=cloudcover,
                collection=feature['collection'],
                epsg=feature['properties']['proj:epsg'],
            )
            captures.append(capture)

    return captures
