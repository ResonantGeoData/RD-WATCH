from uuid import uuid4

import pytest
from ninja.testing import TestClient

from django.core.cache import cache

from rdwatch.models import ModelRun
from rdwatch.views.vector_tile import _get_vector_tile_cache_key


@pytest.mark.django_db
def test_vector_tile_cache(test_client: TestClient, model_run: ModelRun) -> None:
    assert model_run.evaluations.count() == 0

    cache_key = _get_vector_tile_cache_key(model_run.id, 0, 0, 0, model_run.created)

    assert cache.get(cache_key) is None

    test_client.get(f'/model-runs/{model_run.id}/vector-tile/0/0/0.pbf/')

    # There should be a cache hit now that the endpoint has been hit
    assert cache.get(cache_key) is not None


@pytest.mark.django_db
def test_vector_tile_cache_nonexistant_model_run(test_client: TestClient) -> None:
    non_existant_model_run_id = uuid4()

    resp = test_client.get(
        f'/model-runs/{non_existant_model_run_id}/vector-tile/0/0/0.pbf/'
    )

    assert resp.status_code == 404
