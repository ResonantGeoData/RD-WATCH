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
    assert image
    # TODO: Uncomment when S3 credentials on CI are fixed
    # with yeild_tilesource_from_image(image) as src:
    #     assert src.getMetadata()


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


@pytest.mark.django_db(transaction=True)
def test_stac_rest_list(authenticated_api_client, stac_file_factory):
    # Create 3 stac files
    stac_file_factory()
    stac_file_factory()
    stac_file = stac_file_factory()
    checksum_file = stac_file.file

    # Baseline
    r = authenticated_api_client.get('/api/watch/stac_file')
    assert r.json()['count'] == 3
    assert len(r.json()['results']) == 3

    # Assert filtering by checksum file gives one result
    r = authenticated_api_client.get('/api/watch/stac_file', {'file': checksum_file.id})
    assert r.json()['count'] == 1
    assert r.json()['results'][0]['id'] == stac_file.id
    assert r.json()['results'][0]['file']['id'] == checksum_file.id

    # Assert nothing returned for non-existant checksum file
    r = authenticated_api_client.get('/api/watch/stac_file', {'file': -1})
    assert r.json()['count'] == 0
    assert not r.json()['results']
