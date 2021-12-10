from pathlib import Path

import pytest
from rgd_imagery.large_image_utilities import yeild_tilesource_from_image

from . import factories


def get_data_path(name):
    return Path(__file__).absolute().parent / 'data' / name


@pytest.mark.parametrize(
    'sample_file',
    ['landsat-c2l1.json', 'landsat-c2l2-sr.json'],
)
@pytest.mark.django_db(transaction=True)
def test_landsat_stac_support(sample_file):
    stac_file = factories.STACFileFactory(
        file__file__filename=sample_file,
        file__file__from_path=get_data_path(sample_file),
    )
    stac_file.refresh_from_db()
    assert stac_file.raster
    assert stac_file.raster.image_set.images.count()

    # Make sure the image is reachable
    image = stac_file.raster.image_set.images.first()
    with yeild_tilesource_from_image(image) as src:
        assert src.getMetadata()


@pytest.mark.parametrize(
    'sample_file',
    ['sentinel-s2-l1c.json', 'sentinel-s2-l2a.json'],
)
@pytest.mark.django_db(transaction=True)
def test_sentinel_stac_support(sample_file):
    stac_file = factories.STACFileFactory(
        file__file__filename=sample_file,
        file__file__from_path=get_data_path(sample_file),
    )
    stac_file.refresh_from_db()
    assert stac_file.raster
    assert stac_file.raster.image_set.images.count()

    # Make sure the image is reachable
    image = stac_file.raster.image_set.images.first()
    with yeild_tilesource_from_image(image) as src:
        assert src.getMetadata()
