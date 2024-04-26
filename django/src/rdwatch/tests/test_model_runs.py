from datetime import timedelta
from uuid import uuid4

import pytest
from freezegun import freeze_time
from ninja.testing import TestClient

from django.utils import timezone

from rdwatch.models import ModelRun, Performer, Region
from rdwatch.tasks import collect_garbage_task


@pytest.mark.django_db(databases=['default'])
def test_model_run_auto_delete(region: Region) -> None:
    # Create a model run with expiration time of an hour ago
    with freeze_time(timezone.now() - timedelta(hours=2)):
        ModelRun.objects.create(
            title='test1',
            parameters={},
            region=region,
            performer=Performer.objects.all().first(),
            expiration_time=timedelta(hours=1),
        )
    not_expired_model_run = ModelRun.objects.create(
        title='test2',
        parameters={},
        region=region,
        performer=Performer.objects.all().first(),
        expiration_time=timedelta(hours=2),
    )
    model_run_with_no_expiration = ModelRun.objects.create(
        title='test3',
        parameters={},
        region=region,
        performer=Performer.objects.all().first(),
    )
    assert ModelRun.objects.count() == 3

    collect_garbage_task()

    assert ModelRun.objects.count() == 2
    assert list(ModelRun.objects.all()) == [
        not_expired_model_run,
        model_run_with_no_expiration,
    ]


@pytest.mark.django_db
def test_model_run_rest_create(test_client: TestClient, region_id: str) -> None:
    performer = Performer.objects.first()
    title = 'test'

    assert (
        ModelRun.objects.filter(
            title=title, performer=performer, region__name=region_id
        ).count()
        == 0
    )

    res = test_client.post(
        '/model-runs/',
        json={
            'performer': performer.short_code,
            'title': title,
            'region': region_id,
            'parameters': {},
        },
    )

    assert res.status_code == 200
    assert res.json()['title'] == title
    assert res.json()['performer']['short_code'] == performer.short_code
    assert (
        ModelRun.objects.filter(
            title=title, performer=performer, region__name=region_id
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_model_run_rest_list(test_client: TestClient, region: Region) -> None:
    # Create test data
    performers = list(Performer.objects.all())
    model_runs = ModelRun.objects.bulk_create(
        ModelRun(performer=performer, title=f'test_{i}', region=region, parameters={})
        for i, performer in enumerate(performers)
    )

    # Test with no filters
    res = test_client.get('/model-runs/')
    assert res.status_code == 200
    assert res.json()['count'] == len(model_runs)
    assert {
        (mr['title'], mr['performer']['short_code']) for mr in res.json()['items']
    } == {(mr.title, mr.performer.short_code) for mr in model_runs}

    # Test performer filter
    for performer in performers:
        res = test_client.get(f'/model-runs/?performer={performer.short_code}')
        assert res.status_code == 200
        assert [mr['title'] for mr in res.json()['items']] == [
            mr.title for mr in model_runs if mr.performer == performer
        ]

    # Test region filter
    new_region = Region.objects.create(name='YY_R001')
    new_region_model_runs = ModelRun.objects.bulk_create(
        [
            ModelRun(
                performer=performers[0],
                title='DifferentRegion',
                region=new_region,
                parameters={},
            )
            for _ in range(20)
        ]
    )
    res = test_client.get(f'/model-runs/?region={new_region.name}')
    assert res.status_code == 200
    assert {item['id'] for item in res.json()['items']} == {
        str(m.id) for m in new_region_model_runs
    }


@pytest.mark.django_db
def test_model_run_rest_get(test_client: TestClient, region: Region) -> None:
    # Create test data
    performer = Performer.objects.first()
    title = 'test'
    model_run = ModelRun.objects.create(
        performer=performer,
        title=title,
        region=region,
        parameters={},
    )

    # Get model run that exists
    res = test_client.get(f'/model-runs/{model_run.id}/')
    assert res.json()['id'] == str(model_run.id)
    assert res.json()['performer']['id'] == performer.id
    assert res.json()['performer']['short_code'] == performer.short_code

    # Get model run that doesn't exist
    res = test_client.get(f'/model-runs/{uuid4()}/')
    assert res.status_code == 404
