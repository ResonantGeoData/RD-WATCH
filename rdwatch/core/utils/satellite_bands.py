import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta

from pystac import Item

from rdwatch.core.models.lookups import CommonBand, ProcessingLevel
from rdwatch.core.utils.capture import STACCapture
from rdwatch.core.utils.stac_search import COLLECTIONS, SOURCES, stac_search

logger = logging.getLogger(__name__)

RED_GREEN_BLUE = ['red', 'green', 'blue']


@dataclass
class Band(STACCapture):
    constellation: str
    spectrum: CommonBand
    level: ProcessingLevel
    timestamp: datetime
    bbox: tuple[float, float, float, float]
    cloudcover: int
    collection: str


def update_assets_prefer_s3(item: Item):
    """Update an Item's Assets' href to point to s3 if available."""
    for asset in item.assets.values():
        match asset.extra_fields:
            case {'alternate': {'s3': {'href': uri}}}:
                asset.href = uri


def get_bands(
    constellation: str,
    timestamp: datetime,
    bbox: tuple[float, float, float, float],
    timebuffer: timedelta | None = None,
) -> Iterator[Band]:
    if constellation not in SOURCES:
        raise ValueError(f'Unsupported constellation {constellation}')

    results = stac_search(
        constellation,
        timestamp,
        bbox,
        timebuffer=timebuffer or timedelta(hours=1),
    )

    level, _ = ProcessingLevel.objects.get_or_create(
        slug='2A',
        defaults={'description': 'surface reflectance'},
    )

    for item in results.items():
        timestr = item.properties.get('datetime')
        if not timestr:
            logger.warning("Malformed STAC response: no 'properties.datetime'")
            continue

        timestamp = datetime.fromisoformat(timestr.rstrip('Z'))
        stac_bbox = item.bbox

        if item.collection_id not in COLLECTIONS:
            logger.warning(
                'Malformed STAC response: unknown collection %s', item.collection_id
            )
            continue

        # Prefer S3 URIs. Do this before passing the item to STACReader
        # so that STACReader will read the S3 URIs.
        update_assets_prefer_s3(item)

        cloudcover = item.properties.get('eo:cloud_cover', 0)
        has_visual_band = False

        for name, asset in item.assets.items():
            if name == 'visual' or 'visual' in asset.roles:
                has_visual_band = True
                spectrum = CommonBand.objects.get(slug='visual')
            else:
                match asset.extra_fields:
                    case {'eo:bands': [{'common_name': common_name}]}:
                        spectrum = CommonBand.objects.get(slug=common_name)
                    case _:
                        continue

            yield Band(
                constellation=constellation,
                timestamp=timestamp,
                level=level,
                spectrum=spectrum,
                bbox=stac_bbox,
                cloudcover=cloudcover,
                collection=item.collection_id,
                stac_item=item,
                stac_assets={name},
            )

        # Combine red/green/blue together to make our own visual band
        # if we didn't encounter a visual band.
        if (
            not has_visual_band
            and 'red' in item.assets
            and 'green' in item.assets
            and 'blue' in item.assets
        ):
            yield Band(
                constellation=constellation,
                timestamp=timestamp,
                level=level,
                spectrum=CommonBand.objects.get(slug='visual'),
                bbox=stac_bbox,
                cloudcover=cloudcover,
                collection=item.collection_id,
                stac_item=item,
                stac_assets=set(RED_GREEN_BLUE),
            )
