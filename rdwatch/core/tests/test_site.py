import json

import pytest
from ninja.testing import TestClient

from rdwatch.core.models import SiteEvaluation
from rdwatch.core.views.site import SiteImageSiteDetailResponse


@pytest.mark.django_db
def test_site_details_rest(
    test_client: TestClient, site_evaluation: SiteEvaluation
) -> None:
    response = test_client.get(f'/sites/{site_evaluation.id}/details/')
    assert response.status_code == 200

    data = response.json()
    assert data == json.loads(
        SiteImageSiteDetailResponse(
            **{
                'configurationId': site_evaluation.configuration_id,
                'title': site_evaluation.configuration.title,
                'timemin': (
                    site_evaluation.start_date.timestamp()
                    if site_evaluation.start_date
                    else None
                ),
                'timemax': (
                    site_evaluation.end_date.timestamp()
                    if site_evaluation.end_date
                    else None
                ),
                'regionName': site_evaluation.configuration.region.name,
                'performer': site_evaluation.configuration.performer.short_code,
                'siteNumber': site_evaluation.number,
                'version': site_evaluation.version,
            }
        ).model_dump_json()
    )
