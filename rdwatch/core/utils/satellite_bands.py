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
    if 'features' not in results:
        logger.info("Malformed STAC response: no 'features'")
        return

    for feature in results['features']:
        if 'assets' not in feature:
            logger.info("Malformed STAC response: no 'assets'")
            continue

        match feature:
            case {'properties': {'datetime': timestr}}:
                timestamp = datetime.fromisoformat(timestr.rstrip('Z'))
            case _:
                logger.info("Malformed STAC response: no 'properties.datetime'")
                continue

        match feature:
            case {'bbox': bbox_lst}:
                stac_bbox = cast(tuple[float, float, float, float], tuple(bbox_lst))
            case _:
                logger.info("Malformed STAC response: no 'bbox'")
                continue

        cloudcover = 0
        match feature:
            case {'collection': collection}:
                if collection in COLLECTIONS:
                    level, _ = ProcessingLevel.objects.get_or_create(
                        slug='2A',
                        defaults={'description': 'surface reflectance'},
                    )
                else:
                    logger.info(
                        'Malformed STAC response: unknown collection ' f"'{collection}'"
                    )
                    continue
            case _:
                logger.info("Malformed STAC response: no 'collection'")
                continue
        if 'properties' in feature.keys():
            if 'eo:cloud_cover' in feature['properties'].keys():
                cloudcover = feature['properties']['eo:cloud_cover']

        for name, asset in feature['assets'].items():
            if name == 'visual':
                spectrum = CommonBand.objects.get(slug='visual')
            else:
                match asset:
                    case {'eo:bands': [{'common_name': common_name}]}:
                        spectrum = CommonBand.objects.get(slug=common_name)
                    case _:
                        continue

            match asset:
                case {'alternate': {'s3': {'href': uri}}}:
                    ...
                case {'href': uri}:
                    ...
                case _:
                    logger.info("Malformed STAC response: no 'href'")
                    continue

            yield Band(
                constellation=constellation,
                timestamp=timestamp,
                level=level,
                spectrum=spectrum,
                bbox=stac_bbox,
                uri=uri,
                cloudcover=cloudcover,
                collection=feature['collection'],
            )
