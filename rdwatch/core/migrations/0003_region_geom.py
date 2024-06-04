# Generated by Django 4.1.5 on 2023-02-28 15:30

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='region',
            name='geom',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                blank=True,
                help_text='Polygon from the associated Region Feature',
                null=True,
                srid=3857,
            ),
        ),
    ]
