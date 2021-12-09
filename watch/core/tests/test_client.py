from typing import Dict
from django.contrib.auth.models import User
import pytest
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


def test_post_stac_file(py_client: WATCHClient):
    file_url = datastore.get_url('astro.png')
    res: Dict = py_client.watch.post_stac_file(url=file_url, name='test')

    # Assert checksum file created
    checksum_file_dict = res['file']
    assert ChecksumFile.objects.filter(id=checksum_file_dict['id']).exists()

    # Assert stack file created
    assert STACFile.objects.filter(id=res['id']).exists()
