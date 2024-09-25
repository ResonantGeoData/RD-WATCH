import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from rdwatch.core.models.lookups import CommonBand, ProcessingLevel
from rdwatch.core.utils.stac_search import stac_search

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Band:
    constellation: str
    spectrum: CommonBand
    level: ProcessingLevel
    timestamp: datetime
    bbox: tuple[float, float, float, float]
    uri: str
    cloudcover: int
    collection: str


COLLECTIONS: list[str] = ['sentinel-2-c1-l2a', 'sentinel-2-l2a', 'landsat-c2-l2']


def get_bands(
    constellation: str,
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> Iterator[Band]:
    if constellation not in ('S2', 'L8', 'PL'):
        raise ValueError(f'Unsupported constellation {constellation}')

    results = stac_search(
        constellation,
        timestamp,
        bbox,
        timebuffer=timebuffer or timedelta(hours=1),
    )

    for item in results.items():
        timestr = item.properties.get('datetime')
        if not timestr:
            logger.warning("Malformed STAC response: no 'properties.datetime'")
            continue

        timestamp = datetime.fromisoformat(timestr.rstrip('Z'))
        stac_bbox = item.bbox

        if item.collection_id not in COLLECTIONS:
            logger.warning("Malformed STAC response: unknown collection %s", item.collection_id)
            continue

        level, _ = ProcessingLevel.objects.get_or_create(
            slug='2A',
            defaults={'description': 'surface reflectance'},
        )

        cloudcover = item.properties.get('eo:cloud_cover', 0)

        for name, asset in item.assets.items():
            if name == 'visual' or 'visual' in asset.roles:
                spectrum = CommonBand.objects.get(slug='visual')
            else:
                match asset.extra_fields:
                    case {'eo:bands': [{'common_name': common_name}]}:
                        spectrum = CommonBand.objects.get(slug=common_name)
                    case _:
                        continue

            match asset.extra_fields:
                case {'alternate': {'s3': {'href': uri}}}:
                    ...
                case _:
                    uri = asset.href

            yield Band(
                constellation=constellation,
                timestamp=timestamp,
                level=level,
                spectrum=spectrum,
                bbox=stac_bbox,
                uri=uri,
                cloudcover=cloudcover,
                collection=item.collection_id,
            )
