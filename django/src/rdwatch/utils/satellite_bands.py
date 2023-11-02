import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from rdwatch.models.lookups import CommonBand, ProcessingLevel
from rdwatch.utils.stac_search import stac_search

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


def get_bands(
    constellation: str,
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> Iterator[Band]:
    if constellation != 'S2' and constellation != 'L8':
        raise ValueError(f'Unsupported constellation {constellation}')

    results = stac_search(
        constellation,
        timestamp,
        bbox,
        timebuffer=timebuffer or timedelta(hours=1),
    )
    if 'features' not in results:
        logger.warning("Malformed STAC response: no 'features'")
        return

    for feature in results['features']:
        if 'assets' not in feature:
            logger.warning("Malformed STAC response: no 'assets'")
            continue

        match feature:
            case {'properties': {'datetime': timestr}}:
                timestamp = datetime.fromisoformat(timestr.rstrip('Z'))
            case _:
                logger.warning("Malformed STAC response: no 'properties.datetime'")
                continue

        match feature:
            case {'bbox': bbox_lst}:
                stac_bbox = cast(tuple[float, float, float, float], tuple(bbox_lst))
            case _:
                logger.warning("Malformed STAC response: no 'bbox'")
                continue

        cloudcover = 0
        match feature:
            case {'collection': 'landsat-c2l1' | 'sentinel-s2-l1c'}:
                level, _ = ProcessingLevel.objects.get_or_create(
                    slug='1C',
                    defaults={'description': 'top of atmosphere radiance'},
                )
            case {'collection': collection}:
                if (
                    collection
                    in (
                        'landsat-c2l2-sr',
                        'sentinel-s2-l2a',
                        'sentinel-s2-l2a-cogs',
                    )
                    or collection.startswith('ta1-s2-acc-')
                    or collection.startswith('ta1-ls-acc-')
                ):
                    level, _ = ProcessingLevel.objects.get_or_create(
                        slug='2A',
                        defaults={'description': 'surface reflectance'},
                    )
                else:
                    logger.warning(
                        'Malformed STAC response: unknown collection ' f"'{collection}'"
                    )
                    continue
            case _:
                logger.warning("Malformed STAC response: no 'collection'")
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
                    logger.warning("Malformed STAC response: no 'href'")
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
