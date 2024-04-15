import pytest
from ninja.testing import TestClient

from rdwatch.models import SiteImage


@pytest.mark.django_db
def test_site_images_rest_list(test_client: TestClient, site_image: SiteImage) -> None:
    response = test_client.get(f'/evaluations/images/{site_image.site.pk}/')
    assert response.status_code == 200

    data = response.json()
    assert len(data['images']['results']) == 1
    assert data['images']['count'] == 1
    # TODO: make more assertions about response
