import pytest
from ninja.testing import TestClient

from rdwatch.models import HyperParameters, SiteEvaluation


@pytest.mark.django_db
def test_site_model_ingest(
    test_client: TestClient,
    hyper_parameters: HyperParameters,
) -> None:
    site_model = {
        'features': [
            {
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                        [
                            [55.505, 24.47],
                            [55.13, 24.97],
                            [55.596, 24.326],
                            [55.901, 24.222],
                            [55.505, 24.47],
                        ]
                    ],
                },
                'properties': {
                    'mgrs': '40RBN',
                    'model_content': 'proposed',
                    'originator': 'kit',
                    'region_id': 'US_R000',
                    'score': 0.85,
                    'site_id': 'US_R000_0000',
                    'status': 'system_confirmed',
                    'type': 'site',
                    'version': '0.0.0',
                },
                'type': 'Feature',
            },
            {
                'geometry': {
                    'coordinates': [
                        [
                            [
                                [55.413, 24.8625],
                                [55.5505, 24.863],
                                [55.4901, 24.864],
                                [55.3596, 24.863],
                                [55.413, 24.8625],
                            ]
                        ],
                        [
                            [
                                [55.413, 24.8625],
                                [55.5505, 24.863],
                                [55.4901, 24.864],
                                [55.3596, 24.863],
                                [55.413, 24.8625],
                            ]
                        ],
                    ],
                    'type': 'MultiPolygon',
                },
                'properties': {
                    'current_phase': 'Site Preparation, Site Preparation',
                    'is_occluded': 'False, False',
                    'is_site_boundary': 'True, True',
                    'score': 0.67,
                    'sensor_name': 'WorldView',
                    'type': 'observation',
                },
                'type': 'Feature',
            },
        ],
        'type': 'FeatureCollection',
    }
    res = test_client.post(
        f'/model-runs/{hyper_parameters.id}/site-model',
        json=site_model,
    )

    assert SiteEvaluation.objects.count() == 1
    assert res.status_code == 201
    assert res.json() == SiteEvaluation.objects.first().id, res.json()


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
