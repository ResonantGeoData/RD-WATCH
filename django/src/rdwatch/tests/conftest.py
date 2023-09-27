from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from ninja.testing import TestClient

from django.core.management import call_command

from rdwatch.api import api
from rdwatch.models import ModelRun
from rdwatch.models.lookups import Performer

if TYPE_CHECKING:
    from pytest_django.plugin import _DatabaseBlocker


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker: _DatabaseBlocker) -> None:
    with django_db_blocker.unblock():
        call_command('loaddata', 'lookups')


@pytest.fixture(scope='session')
def test_client() -> TestClient:
    return TestClient(router_or_app=api)


@pytest.fixture
def model_run() -> ModelRun:
    return ModelRun.objects.create(
        title='Test',
        parameters={},
        performer=Performer.objects.all().first(),
    )
