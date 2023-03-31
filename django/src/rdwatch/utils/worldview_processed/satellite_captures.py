from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from rdwatch.utils.worldview_processed.stac_search import worldview_search


@dataclass()
class WorldViewProcessedCapture:
    timestamp: datetime
    bbox: tuple[float, float, float, float]
    uri: str
    panuri: str | None
    cloudcover: int | None
    collection: str


def get_features(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta,
):
    results = worldview_search(timestamp, bbox, timebuffer=timebuffer)
    yield from results['features']

    matched = results['context']['matched']
    limit = results['context']['limit']
    for i in range(matched // limit):
        page = i + 2
        results = worldview_search(timestamp, bbox, timebuffer=timebuffer, page=page)
        yield from results['features']


def get_captures(
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> list[WorldViewProcessedCapture]:
    if timebuffer is None:
        timebuffer = timedelta(hours=1)

    features = [f for f in get_features(timestamp, bbox, timebuffer=timebuffer)]

    captures = []
    for feature in features:
        if 'visual' in feature['assets']:
            cloudcover = 0
            if 'properties' in feature:
                if 'eo:cloud_cover' in feature['properties']:
                    cloudcover = feature['properties']['eo:cloud_cover']
            capture = WorldViewProcessedCapture(
                timestamp=datetime.fromisoformat(
                    feature['properties']['datetime'].rstrip('Z')
                ),
                bbox=cast(tuple[float, float, float, float], tuple(feature['bbox'])),
                uri=feature['assets']['visual']['href'],
                panuri=None,
                cloudcover=cloudcover,
                collection=feature['collection']
            )
            captures.append(capture)

    # find each vis-multi image's related panchromatic image
    for cap in captures:
        try:
            pan_feature = next(
                feat
                for feat in features
                if feat['properties'].get('nitf:image_representation', False) == 'MONO'
                and datetime.fromisoformat(feat['properties']['datetime'].rstrip('Z'))
                == cap.timestamp
            )
            cap.panuri = pan_feature['assets']['B01']['href']
        except StopIteration:
            continue

    return captures
