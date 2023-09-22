from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations, models

if TYPE_CHECKING:
    from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
    from django.db.migrations.state import StateApps


def migrate_region_name(apps: StateApps, schema_editor: PostGISSchemaEditor):
    Region = apps.get_model('rdwatch', 'Region')  # noqa: N806
    if Region.objects.count() == 0:
        return

    import iso3166

    for region in Region.objects.iterator():
        country_numeric = str(region.country).zfill(3)
        country_code = iso3166.countries_by_numeric[country_numeric].alpha2
        region_number = 'xxx' if region.number is None else str(region.number).zfill(3)
        region.name = f'{country_code}_{region.classification.slug}{region_number}'
        region.save()


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0013_remove_siteevaluation_unique_siteeval'),
    ]

    operations = [
        # Allow column to be NULL initially
        migrations.AddField(
            model_name='region',
            name='name',
            field=models.CharField(max_length=255, null=True),
        ),
        # Populate the `name` column for all existing regions
        migrations.RunPython(migrate_region_name),
        # Now that all `names` are populated, don't allow it to be NULL
        migrations.AlterField(
            model_name='region',
            name='name',
            field=models.CharField(max_length=255, null=False),
        ),
        migrations.RemoveConstraint(
            model_name='region',
            name='uniq_region',
        ),
        migrations.RemoveField(
            model_name='region',
            name='classification',
        ),
        migrations.RemoveField(
            model_name='region',
            name='country',
        ),
        migrations.RemoveField(
            model_name='region',
            name='number',
        ),
        migrations.AddConstraint(
            model_name='region',
            constraint=models.UniqueConstraint(
                fields=('name',),
                name='uniq_region',
                violation_error_message='Region already exists.',
            ),
        ),
        migrations.DeleteModel(
            name='RegionClassification',
        ),
    ]
