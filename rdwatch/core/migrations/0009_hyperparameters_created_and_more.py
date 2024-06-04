from __future__ import annotations

from typing import TYPE_CHECKING

import django_extensions.db.fields

from django.db import migrations, models
from django.db.models import Count, F, OuterRef, Subquery

if TYPE_CHECKING:
    from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
    from django.db.migrations.state import StateApps


def migrate_creation_dates(apps: StateApps, schema_editor: PostGISSchemaEditor):
    HyperParameters = apps.get_model('core', 'HyperParameters')  # noqa: N806
    SiteEvaluation = apps.get_model('core', 'SiteEvaluation')  # noqa: N806

    # Approximate the "created" time of a model run via the oldest timestamp
    # in its evaluations
    qs = HyperParameters.objects.filter(created__isnull=True).annotate(
        created_timestamp=Subquery(
            SiteEvaluation.objects.filter(configuration_id=OuterRef('id'))
            .order_by('timestamp')
            .values('timestamp')[:1]
        )
    )

    # Delete any model runs with zero evaluations
    qs.alias(evaluation_count=Count('evaluations')).filter(evaluation_count=0).delete()

    # Set the "created" times of all remaining model runs
    qs.update(created=F('created_timestamp'))


def reverse_migrate_creation_dates(apps: StateApps, schema_editor: PostGISSchemaEditor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_satellitefetching_celery_id'),
    ]

    operations = [
        # Create "created" column, allowing it to be nullable temporarily
        # while we estimate the creation dates
        migrations.AddField(
            model_name='hyperparameters',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(
                auto_now_add=True,
                default=None,
                null=True,
            ),
            preserve_default=False,
        ),
        # Fill in the creation dates for existing model runs
        migrations.RunPython(
            migrate_creation_dates,
            reverse_migrate_creation_dates,
        ),
        # Set "created" to non-nullable now that all model runs have one
        migrations.AlterField(
            model_name='hyperparameters',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(
                auto_now_add=True,
                default=None,
                null=False,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='hyperparameters',
            name='expiration_time',
            field=models.DurationField(
                blank=True,
                help_text='Time relative to creation that this model run '
                'should be deleted.',
                null=True,
            ),
        ),
    ]
