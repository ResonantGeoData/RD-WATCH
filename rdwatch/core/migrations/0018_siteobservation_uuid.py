# flake8: noqa

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import django.contrib.postgres.indexes
from django.db import migrations, models

if TYPE_CHECKING:
    from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
    from django.db.migrations.state import StateApps


def migrate_site_observations_to_uuid(
    apps: StateApps, schema_editor: PostGISSchemaEditor
):
    SiteObservation = apps.get_model('rdwatch', 'SiteObservation')
    SiteObservationOld = apps.get_model('rdwatch', 'SiteObservationOld')
    SiteObservationTracking = apps.get_model('rdwatch', 'SiteObservationTracking')
    SiteImage = apps.get_model('rdwatch', 'SiteImage')

    for old_obs in SiteObservationOld.objects.iterator():
        new_obs = SiteObservation.objects.create(
            siteeval=old_obs.siteeval,
            label=old_obs.label,
            score=old_obs.score,
            geom=old_obs.geom,
            constellation=old_obs.constellation,
            spectrum=old_obs.spectrum,
            timestamp=old_obs.timestamp,
            notes=old_obs.notes,
        )

        SiteObservationTracking.objects.filter(observation_old=old_obs).update(
            observation=new_obs
        )
        SiteImage.objects.filter(siteobs_old=old_obs).update(siteobs=new_obs)


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0017_siteevaltracking_uuid'),
    ]

    operations = [
        # Rename existing SiteObservation model and foreign key references
        migrations.RenameModel(
            old_name='SiteObservation', new_name='SiteObservationOld'
        ),
        migrations.RenameField(
            model_name='SiteObservationTracking',
            old_name='observation',
            new_name='observation_old',
        ),
        migrations.RenameField(
            model_name='SiteImage', old_name='siteobs', new_name='siteobs_old'
        ),
        # Create new model with UUID primary key
        migrations.CreateModel(
            name='SiteObservation',
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
                ('score', models.FloatField(help_text='Evaluation accuracy')),
                (
                    'geom',
                    django.contrib.gis.db.models.fields.PolygonField(
                        help_text='Footprint of site observation', srid=3857
                    ),
                ),
                (
                    'timestamp',
                    models.DateTimeField(
                        help_text="The source image's timestamp", null=True
                    ),
                ),
                ('notes', models.TextField(blank=True, null=True)),
                (
                    'constellation',
                    models.ForeignKey(
                        help_text="The source image's satellite constellation",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='rdwatch.constellation',
                    ),
                ),
                (
                    'label',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to='rdwatch.observationlabel',
                    ),
                ),
                (
                    'siteeval',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='rdwatch.siteevaluation',
                    ),
                ),
                (
                    'spectrum',
                    models.ForeignKey(
                        help_text="The source image's satellite spectrum",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='rdwatch.commonband',
                    ),
                ),
            ],
            options={
                'default_related_name': 'observations',
            },
        ),
        # Add FKs to new model. Make them nullable initially, until they are populated
        migrations.AddField(
            model_name='siteobservationtracking',
            name='observation',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='base_site_observation',
                to='rdwatch.siteobservation',
            ),
        ),
        migrations.AddField(
            model_name='siteimage',
            name='siteobs',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='rdwatch.siteobservation',
            ),
        ),
        # Migrate data from old model to new one
        migrations.RunPython(migrate_site_observations_to_uuid),
        # Remove temporary columns now that data is migrated
        migrations.RemoveField(
            model_name='siteobservationtracking',
            name='observation_old',
        ),
        migrations.RemoveField(
            model_name='siteimage',
            name='siteobs_old',
        ),
        # Set FK to non-nullable now that data is migrated
        migrations.AlterField(
            model_name='siteobservationtracking',
            name='observation',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='base_site_observation',
                to='rdwatch.siteobservation',
            ),
        ),
        migrations.DeleteModel(name='SiteObservationOld'),
        # Add indexes to new model
        migrations.AddIndex(
            model_name='siteobservation',
            index=django.contrib.postgres.indexes.GistIndex(
                fields=['timestamp'], name='rdwatch_sit_timesta_b3604d_gist'
            ),
        ),
        migrations.AddIndex(
            model_name='siteobservation',
            index=django.contrib.postgres.indexes.GistIndex(
                fields=['score'], name='rdwatch_sit_score_338731_gist'
            ),
        ),
    ]
