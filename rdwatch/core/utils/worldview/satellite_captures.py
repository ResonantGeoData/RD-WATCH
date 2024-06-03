import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, cast

from rdwatch.core.utils.worldview.stac_search import worldview_search

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorldViewImage:
    bits_per_pixel: int
    instrument: Literal['vis-multi', 'panchromatic', 'swir-multi']
    image_representation: Literal['MULTI', 'MONO', 'RGB']
    mission: Literal['WV01', 'GE01', 'WV02', 'WV03', 'WV04']
    timestamp: datetime
    bbox: tuple[float, float, float, float]
    uri: str


@dataclass(frozen=True)
class WorldViewCapture:
    bits_per_pixel: int
    image_representation: Literal['MULTI', 'MONO', 'RGB']
    mission: Literal['WV01', 'GE01', 'WV02', 'WV03', 'WV04']
    timestamp: datetime
    bbox: tuple[float, float, float, float]
    uri: str
    panuri: str | None


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
    window: timedelta | None = None,
    pan_required=False,
) -> list[WorldViewCapture]:
    if timebuffer is None:
        timebuffer = timedelta(hours=1)
    if window is None:
        window = timedelta(days=1)

    images = [
        WorldViewImage(
            mission=feature['properties']['mission'],
            instrument=feature['properties']['instruments'][0],
            image_representation=feature['properties']['nitf:image_representation'],
            bits_per_pixel=feature['properties']['nitf:bits_per_pixel'],
            timestamp=datetime.fromisoformat(
                feature['properties']['datetime'].rstrip('Z')
            ),
            bbox=cast(tuple[float, float, float, float], tuple(feature['bbox'])),
            uri=feature['assets']['data']['href'],
        )
        for feature in get_features(timestamp, bbox, timebuffer=timebuffer)
        if feature['properties']['instruments'][0] in {'vis-multi', 'panchromatic'}
        and feature['properties']['nitf:compression'] == 'NC'
    ]
    images.sort(key=lambda i: i.timestamp)

    # find each vis-multi image's related panchromatic image
    captures: list[WorldViewCapture] = []
    for i, image in enumerate(images):
        if image.instrument == 'vis-multi':
            left = i - 1
            right = i + 1
            while (
                left >= 0
                and images[left].instrument != 'panchromatic'
                and abs(images[left].timestamp - image.timestamp) < timedelta(hours=1)
            ):
                left -= 1
            while (
                right < len(captures)
                and images[right].instrument != 'panchromatic'
                and abs(images[right].timestamp - image.timestamp) < timedelta(hours=1)
            ):
                right += 1

            if left < 0 and right < len(captures):
                candidate_panimg = images[right]
            elif left >= 0 and right >= len(captures):
                candidate_panimg = images[left]
            elif left >= 0 and right < len(captures):
                candidate_panimg = (
                    images[right]
                    if abs(images[right].timestamp - image.timestamp)
                    < abs(images[left].timestamp - image.timestamp)
                    else images[left]
                )
            else:
                candidate_panimg = None

            if candidate_panimg is not None:
                panuri = (
                    candidate_panimg.uri
                    if (
                        candidate_panimg.instrument == 'panchromatic'
                        and abs(candidate_panimg.timestamp - image.timestamp)
                        < timedelta(hours=1)
                    )
                    else None
                )
            else:
                panuri = None

            if not pan_required or panuri is not None:
                captures.append(
                    WorldViewCapture(
                        image_representation=image.image_representation,
                        bits_per_pixel=image.bits_per_pixel,
                        mission=image.mission,
                        timestamp=image.timestamp,
                        bbox=image.bbox,
                        uri=image.uri,
                        panuri=panuri,
                    )
                )

    # choose the best quality capture for each time `window`
    binned_captures: list[WorldViewCapture] = []
    blacklist: set[int] = set()
    for image_representation in ('RGB', 'MULTI'):
        for haspan in (True, False):
            for mission in ('WV04', 'WV03', 'WV02', 'GE01', 'WV01'):
                for i, capture in enumerate(captures):
                    if (
                        i not in blacklist
                        and capture.mission == mission
                        and capture.image_representation == image_representation
                        and (not haspan or capture.panuri is not None)
                    ):
                        blacklist.add(i)
                        binned_captures.append(capture)

                        j = i - 1
                        min_time = capture.timestamp - window
                        while j >= 0 and captures[j].timestamp > min_time:
                            blacklist.add(j)
                            j -= 1

                        j = i + 1
                        max_time = capture.timestamp + window
                        while j < len(captures) and captures[j].timestamp < max_time:
                            blacklist.add(j)
                            j += 1

    binned_captures.sort(key=lambda c: c.timestamp)

    return binned_captures
