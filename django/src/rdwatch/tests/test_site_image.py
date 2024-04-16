import json

import pytest
from deepdiff import DeepDiff
from ninja.testing import TestClient

from rdwatch.models import SiteImage
from rdwatch.models.model_run import ModelRun
from rdwatch.models.region import get_or_create_region
from rdwatch.models.site_evaluation import SiteEvaluation


@pytest.mark.django_db
def test_site_images_rest_list(
    test_client: TestClient,
    site_image: SiteImage,
) -> None:
    # Create Ground Truth site that's *not* associated with the existing proposal site
    non_gt_eval = SiteEvaluation.objects.get(pk=site_image.site.pk)
    non_gt_model_run = ModelRun.objects.get(pk=non_gt_eval.configuration.pk)
    non_gt_model_run.pk = None
    non_gt_model_run.region = get_or_create_region('AA_R999')[0]
    non_gt_model_run.save()
    non_gt_eval.pk = None  # set primary key to none to trigger creation of new object
    non_gt_eval.score = 1.0  # set score to 1.0 to indicate ground truth
    non_gt_eval.configuration = non_gt_model_run
    non_gt_eval.save()

    # Now ensure that the previously created GT site is *not* returned
    response = test_client.get(f'/evaluations/images/{site_image.site.pk}/')
    assert response.status_code == 200
    data = response.json()
    assert len(data['images']['results']) == 1
    assert data['images']['count'] == 1
    assert data['groundTruth'] is None  # no GT associated with this proposal
    assert not DeepDiff(
        data['evaluationGeoJSON'],
        {
            'crs': {'properties': {'name': 'EPSG:4326'}, 'type': 'name'},
            **json.loads(site_image.site.geom.transform(4326, clone=True).geojson),
        },
        ignore_order=True,
        significant_digits=2,  # allow some floating point error
    )

    # Create Ground Truth site for the existing proposal site
    gt_eval = SiteEvaluation.objects.get(pk=site_image.site.pk)
    gt_eval.pk = None  # set primary key to none to trigger creation of new object
    gt_eval.score = 1.0  # set score to 1.0 to indicate ground truth
    gt_eval.save()

    # Now ensure that the associated GT site is returned
    response = test_client.get(f'/evaluations/images/{site_image.site.pk}/')
    data = response.json()
    assert response.status_code == 200
    assert len(data['images']['results']) == 1
    assert data['images']['count'] == 1
    assert not DeepDiff(
        data['groundTruth']['geoJSON'],
        {
            'crs': {'properties': {'name': 'EPSG:4326'}, 'type': 'name'},
            **json.loads(gt_eval.geom.transform(4326, clone=True).geojson),
        },
        ignore_order=True,
        significant_digits=2,  # allow some floating point error
    )
