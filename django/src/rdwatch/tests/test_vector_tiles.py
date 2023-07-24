import pytest
from ninja.testing import TestClient

from django.core.cache import cache

from rdwatch.models import HyperParameters
from rdwatch.views.vector_tile import _get_vector_tile_cache_key


@pytest.mark.django_db
def test_vector_tile_cache(
    test_client: TestClient, hyper_parameters: HyperParameters
) -> None:
    assert hyper_parameters.evaluations.count() == 0

    cache_key = _get_vector_tile_cache_key(
        hyper_parameters.id, 0, 0, 0, hyper_parameters.created
    )

    assert cache.get(cache_key) is None

    test_client.get(f'/model-runs/{hyper_parameters.id}/vector-tile/0/0/0.pbf/')

    # There should be a cache hit now that the endpoint has been hit
    assert cache.get(cache_key) is not None


@pytest.mark.django_db
def test_vector_tile_cache_nonexistant_model_run(test_client: TestClient) -> None:
    non_existant_model_run_id = 100

    resp = test_client.get(
        f'/model-runs/{non_existant_model_run_id}/vector-tile/0/0/0.pbf/'
    )

    assert resp.status_code == 404
