from __future__ import annotations

from typing import TYPE_CHECKING

import django.contrib.gis.db.models.fields
from django.contrib.gis.geos import MultiPolygon
from django.db import migrations

if TYPE_CHECKING:
    from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
    from django.db.migrations.state import StateApps


def migrate_observation_geom(apps: StateApps, schema_editor: PostGISSchemaEditor):
    SiteEvaluation = apps.get_model('rdwatch', 'SiteEvaluation')  # noqa: N806
    SiteObservation = apps.get_model('rdwatch', 'SiteObservation')  # noqa: N806

    # Set of SiteEvaluation ids that we want to delete
    evals_to_delete: set[int] = set()

    for observation in SiteObservation.objects.iterator():
        if len(observation.geom_old) > 1:
            # If this MultiPolygon contains more than one Polygon, this
            # site needs to be reingested
            evals_to_delete.add(observation.siteeval.id)
            observation.delete()
        else:
            # Otherwise, extract the one Polygon from the MultiPolygon
            observation.geom = list(observation.geom_old)[0]
            observation.save(update_fields=['geom'])

    SiteEvaluation.objects.filter(id__in=evals_to_delete).delete()


def reverse_migrate_observation_geom(
    apps: StateApps, schema_editor: PostGISSchemaEditor
):
    SiteObservation = apps.get_model('rdwatch', 'SiteObservation')  # noqa: N806

    for observation in SiteObservation.objects.iterator():
        observation.geom_old = MultiPolygon([observation.geom])
        observation.save()


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0004_alter_region_geom'),
    ]

    operations = [
        # Rename current geom column so we can create the new one
        migrations.RenameField('siteobservation', old_name='geom', new_name='geom_old'),
        # Make the old geom column nullable
        migrations.AlterField(
            model_name='siteobservation',
            name='geom_old',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                help_text='Footprint of site observation',
                srid=3857,
                null=True,
            ),
        ),
        # Create the new geom column
        migrations.AddField(
            model_name='siteobservation',
            name='geom',
            field=django.contrib.gis.db.models.fields.PolygonField(
                help_text='Footprint of site observation',
                srid=3857,
                null=True,
            ),
        ),
        # Perform the data migration from the old column to the new one
        migrations.RunPython(
            migrate_observation_geom,
            reverse_migrate_observation_geom,
        ),
        # Now that the data migration is complete, set the new column to be non-nullable
        migrations.AlterField(
            model_name='siteobservation',
            name='geom',
            field=django.contrib.gis.db.models.fields.PolygonField(
                help_text='Footprint of site observation',
                srid=3857,
                null=False,
            ),
        ),
        # Finally, remove the old column
        migrations.RemoveField(
            model_name='siteobservation',
            name='geom_old',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                help_text='Footprint of site observation',
                srid=3857,
            ),
        ),
    ]
