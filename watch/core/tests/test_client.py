from pathlib import Path
from typing import Dict

from django.contrib.auth.models import User
import pytest
from rest_framework.authtoken.models import Token
from rgd.models import ChecksumFile
from rgd_client import create_rgd_client
from rgd_imagery.large_image_utilities import yeild_tilesource_from_image
from rgd_watch_client import WATCHClient

from watch.core.models import STACFile

from . import factories


@pytest.fixture
def py_client(live_server):
    params = {'username': 'test@kitware.com', 'email': 'test@kitware.com', 'password': 'password'}
    user = User.objects.create_user(is_staff=True, is_superuser=True, **params)
    user.save()

    # use constant value for API key so this client fixture can be reused across multiple tests
    Token.objects.create(user=user, key='topsecretkey')

    client = create_rgd_client(
        username=params['username'], password=params['password'], api_url=f'{live_server.url}/api'
    )

    return client


@pytest.fixture
def stac_file():
    file_path = Path(__file__).absolute().parent / 'data' / 'landsat-c2l1.json'
    sfile = factories.STACFileFactory(
        file__file__filename='landsat-c2l1.json',
        file__file__from_path=file_path,
    )
    sfile.refresh_from_db()
    return sfile


def test_get_stac_file(py_client: WATCHClient, stac_file: STACFile):
    res: Dict = py_client.watch.get_stac_file(id=stac_file.id)
    assert res['id'] == stac_file.id


def test_list_stac_file(py_client: WATCHClient, stac_file: STACFile):
    res: Dict = py_client.watch.list_stac_file()

    # Assert that stac file is returned
    assert next((f for f in res['results'] if f['id'] == stac_file.id), None)


def test_post_stac_file(py_client: WATCHClient):
    file_url = 'https://landsatlook.usgs.gov/stac-server/collections/landsat-c2l1/items/LC08_L1GT_227122_20211204_20211204_02_T2'  # noqa
    res: Dict = py_client.watch.post_stac_file(
        url=file_url, name='LC08_L1GT_227122_20211204_20211204_02_T2'
    )

    # Assert checksum file created
    checksum_file_dict = res['file']
    assert ChecksumFile.objects.filter(id=checksum_file_dict['id']).exists()

    # Assert stack file created
    assert STACFile.objects.filter(id=res['id']).exists()

    # Assert imagery was ingested
    stac_file = STACFile.objects.get(id=res['id'])
    assert stac_file.raster
    assert stac_file.raster.image_set.images.count()

    # Make sure the image is reachable
    image = stac_file.raster.image_set.images.first()
    with yeild_tilesource_from_image(image) as src:
        assert src.getMetadata()


def test_reprocess_stac_file(py_client: WATCHClient, stac_file: STACFile):
    before_modified = stac_file.modified.isoformat().replace('+00:00', 'Z')
    before_status = stac_file.status

    res: Dict = py_client.watch.reprocess_stac_file(id=stac_file.id)

    # Assert status and last modified date have changed, signaling a save
    assert res['status'] != before_status
    assert res['modified'] != before_modified
