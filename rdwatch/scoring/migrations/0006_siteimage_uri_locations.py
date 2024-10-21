# Generated by Django 5.0.9 on 2024-10-16 15:17

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('scoring', '0005_animationmodelrunexport_animationsiteexport'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteimage',
            name='uri_locations',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=2048),
                default=list,
                help_text='Links to base files used to construct this image',
                size=None,
            ),
        ),
    ]