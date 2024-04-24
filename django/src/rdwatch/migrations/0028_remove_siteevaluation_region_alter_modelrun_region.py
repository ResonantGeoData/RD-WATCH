# Generated by Django 5.0.3 on 2024-04-24 10:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0027_migrate_regions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteevaluation',
            name='region',
        ),
        migrations.AlterField(
            model_name='modelrun',
            name='region',
            field=models.ForeignKey(
                help_text='The region this model run belongs to',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='model_runs',
                to='rdwatch.region',
            ),
        ),
    ]
