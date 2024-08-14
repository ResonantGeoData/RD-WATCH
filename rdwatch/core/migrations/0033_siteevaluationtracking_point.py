# Generated by Django 5.0.3 on 2024-08-14 11:14

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0032_siteevaluation_point_siteobservation_point_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteevaluationtracking',
            name='point',
            field=django.contrib.gis.db.models.fields.PointField(
                help_text="Point from this site's Site Feature", null=True, srid=3857
            ),
        ),
    ]
