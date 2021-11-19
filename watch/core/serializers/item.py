from decimal import Decimal
import json

from bidict import bidict
import dateutil.parser
from django.contrib.gis.geos import Polygon
from django.db import transaction
import pystac
from pystac.extensions.eo import Band, EOExtension
from pystac.extensions.projection import ProjectionExtension
from rgd.models import ChecksumFile, FileSourceType
from rgd.utility import get_or_create_no_commit
from rgd_imagery import models
from rgd_imagery.models.base import Image
from rgd_imagery.stac.serializers import ItemSerializer as ReadOnlyItemSerializer

BAND_RANGE_BY_COMMON_NAMES = bidict(
    {
        'coastal': (Decimal(0.40), Decimal(0.45)),
        'blue': (Decimal(0.45), Decimal(0.50)),
        'green': (Decimal(0.50), Decimal(0.60)),
        'red': (Decimal(0.60), Decimal(0.70)),
        'yellow': (Decimal(0.58), Decimal(0.62)),
        'pan': (Decimal(0.50), Decimal(0.70)),
        'rededge': (Decimal(0.70), Decimal(0.79)),
        'nir': (Decimal(0.75), Decimal(1.00)),
        'nir08': (Decimal(0.75), Decimal(0.90)),
        'nir09': (Decimal(0.85), Decimal(1.05)),
        'cirrus': (Decimal(1.35), Decimal(1.40)),
        'swir16': (Decimal(1.55), Decimal(1.75)),
        'swir22': (Decimal(2.10), Decimal(2.30)),
        'lwir': (Decimal(10.5), Decimal(12.5)),
        'lwir11': (Decimal(10.5), Decimal(11.5)),
        'lwir12': (Decimal(11.5), Decimal(12.5)),
    }
)


def non_unique_get_or_create(model, **kwargs):
    # We are assuming these are unique, but this isn't enforced
    query = model.objects.filter(**kwargs)
    if query.exists():
        return query.first()
    instance = model(**kwargs)
    instance.save()
    return instance


def make_band_meta(eo_band: Band, image: models.Image):
    if eo_band.name.startswith('B') and eo_band.name[1:].isdigit():
        eo_band_number = int(eo_band.name[1:])
    else:
        eo_band_number = 0  # TODO: confirm reasonable default here
    bandmeta = non_unique_get_or_create(
        models.BandMeta,
        parent_image=image,
        band_number=eo_band_number,
    )
    bandmeta.description = eo_band.description
    if eo_band.common_name and eo_band.common_name in BAND_RANGE_BY_COMMON_NAMES:
        eo_band_spectral_lower, eo_band_spectral_upper = BAND_RANGE_BY_COMMON_NAMES[
            eo_band.common_name
        ]
        bandmeta.band_range = (
            eo_band_spectral_lower,
            eo_band_spectral_upper,
        )
    elif eo_band.center_wavelength and eo_band.full_width_half_max:
        eo_band_spectral_upper = (
            Decimal(eo_band.center_wavelength) + Decimal(eo_band.full_width_half_max) / 2
        )
        eo_band_spectral_lower = eo_band_spectral_upper - Decimal(eo_band.full_width_half_max) / 2
        bandmeta.band_range = (
            eo_band_spectral_lower,
            eo_band_spectral_upper,
        )
    bandmeta.save()
    return bandmeta


class ItemSerializer(ReadOnlyItemSerializer):
    @transaction.atomic
    def create(self, data):
        item = pystac.Item.from_dict(data)
        item_eo_ext = EOExtension.ext(item, add_if_missing=True)
        proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
        image_ids, ancillary = [], []
        for key, asset in item.assets.items():
            checksum_file = non_unique_get_or_create(
                ChecksumFile,
                type=FileSourceType.URL,
                url=asset.href,
            )
            if (
                len(item.assets) == 1
                or (asset.roles and 'data' in asset.roles)
                or key.startswith('data')
            ):
                image = non_unique_get_or_create(Image, file=checksum_file)
                image_ids.append(image.pk)
                if item_eo_ext.bands:
                    for eo_band in item_eo_ext.bands:
                        bandmeta = make_band_meta(eo_band, image)
                        bandmeta.save()
            else:
                ancillary.append(checksum_file)

        image_set, _ = models.get_or_create_image_set(image_ids, defaults=dict(name=item.id))

        raster, raster_created = get_or_create_no_commit(
            models.Raster, image_set=image_set, defaults=dict(name=item.id)
        )
        raster.skip_signal = True
        raster.save()
        [raster.ancillary_files.add(af) for af in ancillary]
        raster.save()

        outline = Polygon(
            (
                [item.bbox[0], item.bbox[1]],
                [item.bbox[0], item.bbox[3]],
                [item.bbox[2], item.bbox[3]],
                [item.bbox[2], item.bbox[1]],
                [item.bbox[0], item.bbox[1]],
            )
        )

        raster_meta = dict(
            footprint=json.dumps(item.geometry),
            crs=f'+init=epsg:{proj_ext.epsg}',
            cloud_cover=item_eo_ext.cloud_cover,
            transform=(proj_ext.transform or [0.0] * 6),  # TODO: fix default
            extent=item.bbox,
            origin=(item.bbox[0], item.bbox[1]),
            resolution=(0, 0),  # TODO: fix
            outline=outline,
            acquisition_date=dateutil.parser.isoparser().isoparse(item.properties['datetime']),
            instrumentation=item.properties['platform'],
        )

        if raster_created:
            instance = models.RasterMeta(**raster_meta)
            instance.parent_raster = raster
        else:
            models.RasterMeta.objects.filter(parent_raster=raster).update(**raster_meta)
            instance = models.RasterMeta.objects.get(parent_raster=raster)
        instance.save()

        return instance
