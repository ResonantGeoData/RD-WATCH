from datetime import datetime, timedelta
from typing import Any

import pytest
from ninja.testing import TestClient
from pydantic import BaseModel

from rdwatch.models import ModelRun, SiteEvaluation, SiteObservation


@pytest.fixture
def site_model_json() -> dict[str, Any]:
    """A valid site model JSON."""
    return {
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
                    'observation_date': '2010-01-01',
                    'sensor_name': 'WorldView',
                    'type': 'observation',
                },
                'type': 'Feature',
            },
        ],
        'type': 'FeatureCollection',
    }


@pytest.mark.django_db(databases=['default'])
def test_site_model_ingest(
    site_model_json: dict[str, Any],
    test_client: TestClient,
    model_run: ModelRun,
) -> None:
    res = test_client.post(
        f'/model-runs/{model_run.id}/site-model/',
        json=site_model_json,
    )

    assert SiteEvaluation.objects.count() == 1
    assert res.status_code == 201
    assert res.json() == str(SiteEvaluation.objects.first().id), res.json()


@pytest.mark.django_db(databases=['default'])
def test_site_model_ingest_missing_scores(
    site_model_json: dict[str, Any],
    test_client: TestClient,
    model_run: ModelRun,
) -> None:
    """
    Test that a site model containing sites/observations with missing
    scores ingest properly.
    """
    # Remove `score` fields
    for feature in site_model_json['features']:
        del feature['properties']['score']

    res = test_client.post(
        f'/model-runs/{model_run.id}/site-model/',
        json=site_model_json,
    )
    assert res.status_code == 201
    assert SiteEvaluation.objects.count() > 0
    assert SiteObservation.objects.count() > 0

    # Score should default to 1.0 if missing from the site model json -
    assert all(obs.score == 1.0 for obs in SiteObservation.objects.all())
    assert all(eval.score == 1.0 for eval in SiteEvaluation.objects.all())


@pytest.mark.django_db(databases=['default'])
def test_site_model_ingest_malformed_geometry(
    test_client: TestClient,
    model_run: ModelRun,
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
        f'/model-runs/{model_run.id}/site-model/',
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


@pytest.fixture
def sample_region_model(region_id: str) -> dict[str, Any]:
    # Define a Pydantic model to represent the structure of the sample region model
    class SampleRegionModel(BaseModel):
        type: str = 'FeatureCollection'
        features: list[dict[str, Any]]

    # Define a sample region feature using the information from the RegionFeature class
    sample_region_feature = {
        'type': 'Feature',
        'properties': {
            'type': 'region',
            'region_id': f'{region_id}',
            'version': '1.0',
            'mgrs': 'ABC123',
            'model_content': 'annotation',
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'originator': 'te',
            'comments': 'Sample comments',
            'performer_cache': None,
        },
        'geometry': {
            'type': 'Polygon',
            'coordinates': [
                [
                    [-104.05, 48.99],
                    [-97.22, 48.98],
                    [-96.98, 45.94],
                    [-104.03, 45.94],
                    [-104.05, 48.99],
                ]
            ],
        },
    }

    # Define a sample site summary feature using the information
    # from the SiteSummaryFeature class
    sample_site_summary_feature = {
        'type': 'Feature',
        'properties': {
            'type': 'site_summary',
            'site_id': f'{region_id}_0001',
            'version': '1.0',
            'mgrs': 'ABC123',
            'status': 'positive_annotated',
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'model_content': 'annotation',
            'originator': 'te',
            'comments': None,
            'score': 0.8,
            'validated': 'True',
            'annotation_cache': None,
        },
        'geometry': {
            'type': 'Polygon',
            'coordinates': [
                [
                    [-104.05, 48.99],
                    [-97.22, 48.98],
                    [-96.98, 45.94],
                    [-104.03, 45.94],
                    [-104.05, 48.99],
                ]
            ],
        },
    }

    # Combine the sample region feature and sample site summary
    # feature into the features list
    sample_region_model = SampleRegionModel(
        features=[sample_region_feature, sample_site_summary_feature]
    )

    # Return the sample region model as a dictionary
    return sample_region_model.dict()


@pytest.mark.django_db
def test_region_model_ingest(
    sample_region_model: dict[str, Any],
    test_client: TestClient,
    model_run: ModelRun,
) -> None:
    res = test_client.post(
        f'/model-runs/{model_run.id}/region-model/',
        json=sample_region_model,
    )

    assert res.status_code == 201
    assert SiteEvaluation.objects.count() == 1
    assert res.json() == [str(SiteEvaluation.objects.first().id)], res.json()
