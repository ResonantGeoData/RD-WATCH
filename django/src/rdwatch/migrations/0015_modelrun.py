# flake8: noqa

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import django_extensions.db.fields

from django.db import migrations, models

if TYPE_CHECKING:
    from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
    from django.db.migrations.state import StateApps


def migrate_to_model_run(apps: StateApps, schema_editor: PostGISSchemaEditor):
    HyperParameters = apps.get_model('rdwatch', 'HyperParameters')
    ModelRun = apps.get_model('rdwatch', 'ModelRun')
    SiteEvaluation = apps.get_model('rdwatch', 'SiteEvaluation')
    AnnotationExport = apps.get_model('rdwatch', 'AnnotationExport')

    for hyper_parameters in HyperParameters.objects.iterator():
        model_run = ModelRun.objects.create(
            created=hyper_parameters.created,
            title=hyper_parameters.title,
            performer=hyper_parameters.performer,
            parameters=hyper_parameters.parameters,
            evaluation=hyper_parameters.evaluation,
            evaluation_run=hyper_parameters.evaluation_run,
            expiration_time=hyper_parameters.expiration_time,
            proposal=hyper_parameters.proposal,
            ground_truth=hyper_parameters.ground_truth,
        )

        SiteEvaluation.objects.filter(configuration_old=hyper_parameters).update(
            configuration=model_run
        )
        AnnotationExport.objects.filter(configuration_old=hyper_parameters).update(
            configuration=model_run
        )


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0014_remove_region_uniq_region_and_more'),
    ]

    operations = [
        # Create new model for "model runs" that is identical to
        # HyperParameters except it uses a UUID for primary key.
        # Note, we set `created` to a regular DateTimeField instead
        # of CreationDateTimeField because we want to explicitly
        # set it during the migration of the existing model runs.
        migrations.CreateModel(
            name='ModelRun',
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
                (
                    'created',
                    models.DateTimeField(null=False),
                ),
                ('title', models.CharField(max_length=1000)),
                (
                    'parameters',
                    models.JSONField(
                        db_index=True, help_text='The hyper parameters for an ML task'
                    ),
                ),
                ('evaluation', models.IntegerField(blank=True, null=True)),
                ('evaluation_run', models.IntegerField(blank=True, null=True)),
                (
                    'expiration_time',
                    models.DurationField(
                        blank=True,
                        help_text='Time relative to creation that this model run should be deleted.',
                        null=True,
                    ),
                ),
                (
                    'proposal',
                    models.CharField(
                        blank=True,
                        choices=[('PROPOSAL', 'Proposal'), ('APPROVED', 'Approved')],
                        help_text='Fetching Status',
                        max_length=255,
                        null=True,
                    ),
                ),
                ('ground_truth', models.BooleanField(default=False)),
                (
                    'performer',
                    models.ForeignKey(
                        help_text='The team that produced this evaluation',
                        on_delete=models.deletion.PROTECT,
                        to='rdwatch.performer',
                    ),
                ),
            ],
        ),
        # Rename the FK pointing to `HyperParameters` so we can migrate them to `ModelRun`
        migrations.RenameField(
            model_name='annotationexport',
            old_name='configuration',
            new_name='configuration_old',
        ),
        # Add a new FK pointing at `ModelRun`. Note it is temporarily nullable until we do
        # the data migration.
        migrations.AddField(
            model_name='annotationexport',
            name='configuration',
            field=models.ForeignKey(
                null=True,
                to='ModelRun',
                on_delete=models.PROTECT,
                help_text='The hyper parameters used this site evaluation.',
                db_index=True,
            ),
        ),
        # Rename the FK pointing to `HyperParameters` so we can migrate them to `ModelRun`
        migrations.RenameField(
            model_name='siteevaluation',
            old_name='configuration',
            new_name='configuration_old',
        ),
        # Add a new FK pointing at `ModelRun`. Note it is temporarily nullable until we do
        # the data migration.
        migrations.AddField(
            model_name='siteevaluation',
            name='configuration',
            field=models.ForeignKey(
                null=True,
                to='ModelRun',
                on_delete=models.PROTECT,
                help_text='The hyper parameters used this site evaluation.',
                db_index=True,
            ),
        ),
        # Do the data migration from HyperParameters -> ModelRun in Python
        migrations.RunPython(migrate_to_model_run),
        # Now that all the HyperParameters are converted to ModelRuns, set the `created`
        # field back to `CreationDateTimeField`
        migrations.AlterField(
            model_name='modelrun',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        # Remove the renamed FK columns that point to `HyperParameters`; we don't need them anymore
        migrations.RemoveField(model_name='siteevaluation', name='configuration_old'),
        migrations.RemoveField(model_name='annotationexport', name='configuration_old'),
        # Set the FK to ModelRun to be non-nullable now that they're all migrated
        migrations.AlterField(
            model_name='siteevaluation',
            name='configuration',
            field=models.ForeignKey(
                null=False,
                to='rdwatch.modelrun',
                on_delete=models.PROTECT,
                help_text='The hyper parameters used this site evaluation.',
            ),
        ),
        migrations.AlterField(
            model_name='annotationexport',
            name='configuration',
            field=models.ForeignKey(
                null=False,
                to='rdwatch.modelrun',
                on_delete=models.PROTECT,
                help_text='The hyper parameters used for the xport',
            ),
        ),
    ]
