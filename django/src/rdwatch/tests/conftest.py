from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, get_args

import pytest
from geojson.utils import generate_random as generate_random_geojson
from ninja.testing import TestClient
from pydantic import BaseModel

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.management import call_command

from rdwatch.api import api
from rdwatch.models import ModelRun, Region
from rdwatch.models.lookups import Performer
from rdwatch.models.site_evaluation import SiteEvaluation
from rdwatch.schemas import RegionModel, SiteModel
from rdwatch.schemas.site_model import CurrentPhase

if TYPE_CHECKING:
    from pytest_django.plugin import _DatabaseBlocker

# Define a bounding box for the test region (bounding box of NY State)
_TEST_REGION_BBOX = [-79.762152, 40.496103, -71.856214, 45.01585]


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker: _DatabaseBlocker) -> None:
    with django_db_blocker.unblock():
        call_command('loaddata', 'lookups')


@pytest.fixture(scope='session')
def test_client() -> TestClient:
    return TestClient(router_or_app=api)


@pytest.fixture
def region_polygon() -> Polygon:
    return Polygon.from_bbox(_TEST_REGION_BBOX)


@pytest.fixture
def site_polygon(region_polygon: Polygon) -> Polygon:
    return GEOSGeometry(
        json.dumps(
            generate_random_geojson(
                featureType='Polygon', boundingBox=region_polygon.extent
            )
        )
    )


@pytest.fixture
def observation_polygon(region_polygon: Polygon) -> MultiPolygon:
    return MultiPolygon(
        [
            GEOSGeometry(
                json.dumps(
                    generate_random_geojson(
                        featureType='Polygon', boundingBox=region_polygon.extent
                    )
                )
            )
            for _ in range(5)
        ]
    )


@pytest.fixture
def region_id() -> str:
    return 'KW_R000'


@pytest.fixture
def region(region_id, region_polygon) -> Region:
    return Region.objects.create(
        name=region_id,
        geom=region_polygon,
    )


@pytest.fixture
def model_run(region: Region) -> ModelRun:
    return ModelRun.objects.create(
        title='Test',
        parameters={},
        performer=Performer.objects.all().first(),
        region=region,
    )


@pytest.fixture(
    params=[
        (
            SiteEvaluation.bulk_create_from_site_model,
            SiteModel,
            'site_model_json',
        ),
        (
            SiteEvaluation.bulk_create_from_region_model,
            RegionModel,
            'region_model_json',
        ),
    ]
)
def site_evaluation(
    site_model_json: dict[str, Any],
    model_run: ModelRun,
    request,
) -> SiteEvaluation:
    ingest_func, model_cls, fixture_name = request.param
    siteeval = ingest_func(
        model_cls(**request.getfixturevalue(fixture_name)), model_run
    )
    if isinstance(siteeval, list):
        siteeval = siteeval[0]
    return siteeval


@pytest.fixture
def site_model_json(
    site_polygon: Polygon, observation_polygon: MultiPolygon
) -> dict[str, Any]:
    """A valid site model JSON."""

    # Pad the lengths of these fields to match the observation polygon count
    current_phase: list[str] = list(get_args(CurrentPhase))
    if len(observation_polygon) < len(current_phase):
        current_phase = current_phase[: len(observation_polygon)]
    elif len(observation_polygon) > len(current_phase):
        current_phase = current_phase + ['Unknown'] * (
            len(observation_polygon) - len(current_phase)
        )
    is_occluded = [False] * len(observation_polygon)
    is_site_boundary = [True] * len(observation_polygon)

    return {
        'features': [
            {
                'geometry': json.loads(site_polygon.geojson),
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
                    'start_date': '2023-03-15',
                    'end_date': '2024-04-15',
                },
                'type': 'Feature',
            },
            {
                'geometry': json.loads(observation_polygon.geojson),
                'properties': {
                    'current_phase': ', '.join(current_phase),
                    'is_occluded': ', '.join(map(str, is_occluded)),
                    'is_site_boundary': ', '.join(map(str, is_site_boundary)),
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


@pytest.fixture
def region_model_json(
    region_id: str, region_polygon: Polygon, site_polygon: Polygon
) -> dict[str, Any]:
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
        'geometry': json.loads(region_polygon.geojson),
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
        'geometry': json.loads(site_polygon.geojson),
    }

    # Combine the sample region feature and sample site summary
    # feature into the features list
    sample_region_model = SampleRegionModel(
        features=[sample_region_feature, sample_site_summary_feature]
    )

    # Return the sample region model as a dictionary
    return sample_region_model.dict()
