# Generated by Django 4.1.9 on 2024-01-22 11:22

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0022_rename_siteeval_satellitefetching_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteevaluation',
            name='modified_timestamp',
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                help_text='Timestamp of the last modification',
            ),
            preserve_default=False,
        ),
    ]
