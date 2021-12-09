from typing import Dict
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from rgd.models.mixins import Status
from rgd_client import create_rgd_client
from rgd.datastore import datastore
from rgd.models import ChecksumFile
from rest_framework.authtoken.models import Token


from rgd_watch_client import WATCHClient

from watch.core.models import STACFile


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
    file_path = datastore.fetch('astro.png')
    with open(file_path, 'rb') as file_contents:
        stac_file: STACFile = STACFile.objects.create(
            file=ChecksumFile.objects.create(
                name='astro.png',
                file=SimpleUploadedFile(name='astro.png', content=file_contents.read()),
            ),
        )

    # Manually update status, so it isn't automatically set to QUEUED
    stac_file.status = Status.SKIPPED
    stac_file.save(update_fields=['status'])

    return stac_file


def test_get_stac_file(py_client: WATCHClient, stac_file: STACFile):
    res: Dict = py_client.watch.get_stac_file(id=stac_file.id)
    assert res['id'] == stac_file.id


def test_list_stac_file(py_client: WATCHClient, stac_file: STACFile):
    res: Dict = py_client.watch.list_stac_file()

    # Assert that stac file is returned
    assert next((f for f in res['results'] if f['id'] == stac_file.id), None)


def test_post_stac_file(py_client: WATCHClient):
    file_url = datastore.get_url('astro.png')
    res: Dict = py_client.watch.post_stac_file(url=file_url, name='test')

    # Assert checksum file created
    checksum_file_dict = res['file']
    assert ChecksumFile.objects.filter(id=checksum_file_dict['id']).exists()

    # Assert stack file created
    assert STACFile.objects.filter(id=res['id']).exists()


def test_reprocess_stac_file(py_client: WATCHClient, stac_file: STACFile):
    before_modified = stac_file.modified.isoformat().replace('+00:00', 'Z')
    before_status = stac_file.status

    res: Dict = py_client.watch.reprocess_stac_file(id=stac_file.id)

    # Assert status and last modified date have changed, signaling a save
    assert res['status'] != before_status
    assert res['modified'] != before_modified
