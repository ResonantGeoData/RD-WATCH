import pytest
from ninja.testing import TestClient

from rdwatch.models import HyperParameters


@pytest.mark.django_db
def test_site_model_ingest_malformed_geometry(
    test_client: TestClient,
    hyper_parameters: HyperParameters,
) -> None:
    """
    Test that ensures a malformed geometry gracefully fails (i.e. returns
    a 422 with an informative error instead of a 500 error)
    """
    site_model = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {
                    'type': 'site',
                    'region_id': 'XX_R000',
                    'site_id': 'XX_R001_0000',
                    'version': '2.0.0',
                    'status': 'positive_annotated',
                    'mgrs': '40RBN',
                    'score': 1.0,
                    'start_date': '2023-03-15',
                    'end_date': '2023-03-16',
                    'model_content': 'annotation',
                    'originator': 'kit',
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [],
                },
            },
        ],
    }
    res = test_client.post(
        f'/model-runs/{hyper_parameters.id}/site-model',
        json=site_model,
    )

    assert res.status_code == 422
    assert res.json() == {
        'detail': [
            {
                'loc': ['body', 'site_model', 'features', 0, 'geometry'],
                'msg': 'Failed to parse geometry.',
                'type': 'value_error',
            }
        ]
    }
