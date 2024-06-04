# flake8: noqa

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import django.contrib.postgres.indexes
from django.db import migrations, models

if TYPE_CHECKING:
    from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
    from django.db.migrations.state import StateApps


def migrate_site_obs_to_uuid(apps: StateApps, schema_editor: PostGISSchemaEditor):
    SiteObservationTracking = apps.get_model('core', 'SiteObservationTracking')
    SiteObservationTrackingOld = apps.get_model('core', 'SiteObservationTrackingOld')

    new_obs = []
    for old_obs in SiteObservationTrackingOld.objects.iterator():
        new_obs.append(
            SiteObservationTracking(
                edited=old_obs.edited,
                siteeval=old_obs.siteeval,
                label=old_obs.label,
                score=old_obs.score,
                geom=old_obs.geom,
                observation=old_obs.observation,
                notes=old_obs.notes,
            )
        )

    SiteObservationTracking.objects.bulk_create(new_obs)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0018_siteobservation_uuid'),
    ]

    operations = [
        # Rename existing SiteObservationTracking model and foreign key references
        migrations.RenameModel(
            old_name='SiteObservationTracking', new_name='SiteObservationTrackingOld'
        ),
        # Create a new model with UUID as its primary key
        migrations.CreateModel(
            name='SiteObservationTracking',
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
                ('score', models.FloatField(help_text='Evaluation accuracy')),
                (
                    'geom',
                    django.contrib.gis.db.models.fields.PolygonField(
                        help_text='Footprint of site observation', srid=3857
                    ),
                ),
                ('notes', models.TextField(blank=True, null=True)),
                (
                    'label',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to='core.observationlabel',
                    ),
                ),
                (
                    'observation',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='base_site_observation',
                        to='core.siteobservation',
                    ),
                ),
                (
                    'siteeval',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='core.siteevaluation',
                    ),
                ),
            ],
        ),
        # Migrate data
        migrations.RunPython(migrate_site_obs_to_uuid),
        # Delete the old model
        migrations.DeleteModel(
            name='SiteObservationTrackingOld',
        ),
    ]
