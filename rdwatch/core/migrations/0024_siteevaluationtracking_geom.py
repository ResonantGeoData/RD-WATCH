# Generated by Django 4.1.9 on 2024-01-26 07:56

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0023_siteevaluation_modified_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteevaluationtracking',
            name='geom',
            field=django.contrib.gis.db.models.fields.PolygonField(
                help_text="Polygon from this site's Site Feature", null=True, srid=3857
            ),
        ),
    ]