from datetime import timedelta

import pytest
from freezegun import freeze_time

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
    model_run_to_not_delete = HyperParameters.objects.create(
        title='test2',
        parameters={},
        performer=lookups.Performer.objects.all().first(),
        expiration_time=timedelta(hours=2),
    )
    assert HyperParameters.objects.count() == 2

    delete_temp_model_runs_task()

    assert HyperParameters.objects.count() == 1
    assert HyperParameters.objects.first() == model_run_to_not_delete
