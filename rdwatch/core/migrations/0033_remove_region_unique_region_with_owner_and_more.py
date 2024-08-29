# Generated by Django 5.0.3 on 2024-08-14 13:32

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0032_siteevaluation_point_siteobservation_point_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='region',
            name='unique_region_with_owner',
        ),
        migrations.AddConstraint(
            model_name='region',
            constraint=models.UniqueConstraint(
                condition=models.Q(('owner__isnull', False)),
                fields=('name', 'owner'),
                name='unique_region_with_owner',
                violation_error_message='Region already exists with this name and owner.',
            ),
        ),
    ]