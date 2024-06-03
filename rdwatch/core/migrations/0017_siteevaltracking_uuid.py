# flake8: noqa

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import django.contrib.postgres.indexes
from django.db import migrations, models

if TYPE_CHECKING:
    from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
    from django.db.migrations.state import StateApps


def migrate_site_evals_to_uuid(apps: StateApps, schema_editor: PostGISSchemaEditor):
    SiteEvaluationTracking = apps.get_model('rdwatch', 'SiteEvaluationTracking')
    SiteEvaluationTrackingOld = apps.get_model('rdwatch', 'SiteEvaluationTrackingOld')

    new_evals = []
    for old_eval in SiteEvaluationTrackingOld.objects.iterator():
        new_evals.append(
            SiteEvaluationTracking(
                edited=old_eval.edited,
                evaluation=old_eval.evaluation,
                start_date=old_eval.start_date,
                end_date=old_eval.end_date,
                label=old_eval.label,
                score=old_eval.score,
                notes=old_eval.notes,
            )
        )

    SiteEvaluationTracking.objects.bulk_create(new_evals)


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0016_siteeval_uuid'),
    ]

    operations = [
        # Rename existing SiteEvaluation model and foreign key references
        migrations.RenameModel(
            old_name='SiteEvaluationTracking', new_name='SiteEvaluationTrackingOld'
        ),
        # Create a new model with UUID as its primary key
        migrations.CreateModel(
            name='SiteEvaluationTracking',
            fields=[
                (
                    'id',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ('edited', models.DateTimeField()),
                (
                    'start_date',
                    models.DateTimeField(help_text='Start date in geoJSON', null=True),
                ),
                (
                    'end_date',
                    models.DateTimeField(help_text='end date in geoJSON', null=True),
                ),
                ('score', models.FloatField(help_text='Score of site footprint')),
                ('notes', models.TextField(blank=True, null=True)),
                (
                    'evaluation',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='rdwatch.siteevaluation',
                    ),
                ),
                (
                    'label',
                    models.ForeignKey(
                        help_text='Site feature classification label',
                        on_delete=django.db.models.deletion.PROTECT,
                        to='rdwatch.observationlabel',
                    ),
                ),
            ],
        ),
        # Migrate data
        migrations.RunPython(migrate_site_evals_to_uuid),
        # Make FK non-nullable now that the data migration is complete
        migrations.AlterField(
            model_name='siteevaluationtracking',
            name='evaluation',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to='rdwatch.siteevaluation'
            ),
        ),
        # Delete the old model
        migrations.DeleteModel(
            name='SiteEvaluationTrackingOld',
        ),
    ]
