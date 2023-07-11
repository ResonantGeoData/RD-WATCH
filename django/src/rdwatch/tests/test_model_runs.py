from datetime import timedelta

import pytest
from freezegun import freeze_time
from ninja.testing import TestClient

from django.utils import timezone

from rdwatch.models import HyperParameters, lookups
from rdwatch.tasks import delete_temp_model_runs_task


@pytest.mark.django_db
def test_model_run_auto_delete() -> None:
    # Create a model run with expiration time of an hour ago
    with freeze_time(timezone.now() - timedelta(hours=2)):
        HyperParameters.objects.create(
            title='test1',
            parameters={},
            performer=lookups.Performer.objects.all().first(),
            expiration_time=timedelta(hours=1),
        )
    not_expired_model_run = HyperParameters.objects.create(
        title='test2',
        parameters={},
        performer=lookups.Performer.objects.all().first(),
        expiration_time=timedelta(hours=2),
    )
    model_run_with_no_expiration = HyperParameters.objects.create(
        title='test3',
        parameters={},
        performer=lookups.Performer.objects.all().first(),
    )
    assert HyperParameters.objects.count() == 3

    delete_temp_model_runs_task()

    assert HyperParameters.objects.count() == 2
    assert list(HyperParameters.objects.all()) == [
        not_expired_model_run,
        model_run_with_no_expiration,
    ]


@pytest.mark.django_db
def test_model_run_rest_create(test_client: TestClient) -> None:
    performer = lookups.Performer.objects.first()
    title = 'test'

    assert HyperParameters.objects.filter(title=title, performer=performer).count() == 0

    res = test_client.post(
        '/model-runs/',
        json={
            'performer': performer.slug,
            'title': title,
            'parameters': {},
        },
    )

    assert res.status_code == 200
    assert res.json()['title'] == title
    assert res.json()['performer']['short_code'] == performer.slug
    assert HyperParameters.objects.filter(title=title, performer=performer).count() == 1


@pytest.mark.django_db
def test_model_run_rest_list(test_client: TestClient) -> None:
    # Create test data
    performers = list(lookups.Performer.objects.all())
    model_runs = HyperParameters.objects.bulk_create(
        HyperParameters(performer=performer, title=f'test_{i}', parameters={})
        for i, performer in enumerate(performers)
    )

    # Test with no filters
    res = test_client.get('/model-runs/')
    assert res.status_code == 200
    assert res.json()['count'] == len(model_runs)
    assert {
        (mr['title'], mr['performer']['short_code']) for mr in res.json()['results']
    } == {(mr.title, mr.performer.slug) for mr in model_runs}

    # Test performer filter
    for performer in performers:
        res = test_client.get(f'/model-runs/?performer={performer.slug}')
        assert res.status_code == 200
        assert [mr['title'] for mr in res.json()['results']] == [
            mr.title for mr in model_runs if mr.performer == performer
        ]


@pytest.mark.django_db
def test_model_run_rest_get(test_client: TestClient) -> None:
    # Create test data
    performer = lookups.Performer.objects.first()
    title = 'test'
    model_run = HyperParameters.objects.create(
        performer=performer,
        title=title,
        parameters={},
    )

    # Get model run that exists
    res = test_client.get(f'/model-runs/{model_run.id}/')
    assert res.json()['id'] == model_run.id
    assert res.json()['performer']['id'] == performer.id
    assert res.json()['performer']['short_code'] == performer.slug

    # Get model run that doesn't exist
    res = test_client.get(f'/model-runs/{model_run.id + 1}/')
    assert res.status_code == 404
