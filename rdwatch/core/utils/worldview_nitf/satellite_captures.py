import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from rdwatch.core.utils.capture import URICapture
from rdwatch.core.utils.worldview_nitf.stac_search import worldview_search

logger = logging.getLogger(__name__)


@dataclass()
class WorldViewNITFCapture(URICapture):
    timestamp: datetime
    bbox: tuple[float, float, float, float]
    cloudcover: int | None
    collection: str
    bits_per_pixel: int
    epsg: int
    panuri: int | None
    instruments: list[str]


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
    vis_captures: list[WorldViewNITFCapture] = []
    pan_captures: list[WorldViewNITFCapture] = []
    for feature in features:
        if 'data' in feature['assets']:
            cloudcover = 0
            instruments = []
            if 'properties' in feature:
                if 'eo:cloud_cover' in feature['properties']:
                    cloudcover = feature['properties']['eo:cloud_cover']
                if (
                    'nitf:compression' in feature['properties']
                    and feature['properties']['nitf:compression'] != 'NC'
                ):
                    continue
                if 'instruments' in feature['properties']:
                    instruments = feature['properties']['instruments']
            capture = WorldViewNITFCapture(
                timestamp=datetime.fromisoformat(
                    feature['properties']['datetime'].rstrip('Z')
                ),
                bbox=cast(tuple[float, float, float, float], tuple(feature['bbox'])),
                uri=feature['assets']['data']['href'],
                bits_per_pixel=feature['properties']['nitf:bits_per_pixel'],
                cloudcover=cloudcover,
                collection=feature['collection'],
                instruments=instruments,
                panuri=None,
                epsg=feature['properties']['proj:epsg'],
            )
            if 'panchromatic' in instruments:
                pan_captures.append(capture)
            elif 'vis-multi' in instruments:
                vis_captures.append(capture)
            else:
                logger.info(f'Instrument type {instruments} is no supported')
    # Attempt to add panuri elements to visual captures that exist
    for pan_capture in pan_captures:
        pan_timestamp = pan_capture.timestamp
        for vis_capture in vis_captures:
            vis_timestamp = vis_capture.timestamp
            # Compare bbox and timestamp (within a tolerance for timestamp)
            if abs((vis_timestamp - pan_timestamp).total_seconds()) < 60:
                # If a match is found, update the vis-multi capture's panuri field
                vis_capture.panuri = pan_capture.uri
                break

    return vis_captures
