import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from rdwatch.models.lookups import CommonBand, Constellation, ProcessingLevel
from rdwatch.utils.stac_search import landsat_search, sentinel_search

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Band:
    constellation: Constellation
    spectrum: CommonBand
    level: ProcessingLevel
    timestamp: datetime
    bbox: tuple[float, float, float, float]
    uri: str
    cloudcover: int
    collection: str


def get_bands(
    constellation: Constellation,
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> Iterator[Band]:
    match constellation.slug:
        case 'L8':
            search = landsat_search
        case 'S2':
            search = sentinel_search
        case _:
            raise ValueError(f"Unsupported constellation '{constellation.slug}'")

    page: None | int = 1

    while page is not None:
        results = search(
            timestamp,
            bbox,
            timebuffer=timebuffer or timedelta(hours=1),
            page=page,
        )

        if 'features' not in results:
            logger.warning("Malformed STAC response: no 'features'")
            return

        if 'links' not in results:
            logger.warning("Malformed STAC response: no 'links'")
            return

        next_page = None
        for link in results['links']:
            match link:
                case {'rel': 'next'}:
                    next_page = page + 1
                    break
        page = next_page

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
                case {
                    'collection': 'landsat-c2l2-sr'
                    | 'sentinel-s2-l2a'
                    | 'sentinel-s2-l2a-cogs'
                }:
                    level, _ = ProcessingLevel.objects.get_or_create(
                        slug='2A',
                        defaults={'description': 'surface reflectance'},
                    )
                case {'collection': collection}:
                    logger.warning(
                        f"Malformed STAC response: unkown collection '{collection}'"
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
