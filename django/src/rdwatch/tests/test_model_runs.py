from datetime import timedelta

import pytest
from freezegun import freeze_time

from django.utils import timezone

from rdwatch.models import HyperParameters, lookups
from rdwatch.tasks import delete_temp_model_runs_task


@pytest.mark.django_db(databases=['default'])
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
