# Generated by Django 5.0.3 on 2024-09-23 15:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('scoring', '0004_satellitefetching_rdwatch_sco_status_81a06c_idx'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AnimationModelRunExport',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'export_file',
                    models.FileField(blank=True, default=None, null=True, upload_to=''),
                ),
                (
                    'created',
                    models.DateTimeField(
                        help_text='The zip file export, deleted 1 hour after creation'
                    ),
                ),
                (
                    'name',
                    models.CharField(
                        blank=True,
                        help_text='Name of the model run for download',
                        max_length=1024,
                    ),
                ),
                (
                    'celery_id',
                    models.CharField(
                        blank=True, help_text='Celery Task Id', max_length=255
                    ),
                ),
                ('configuration', models.CharField(max_length=255)),
                ('arguments', models.JSONField(default=None, null=True)),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnimationSiteExport',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'export_file',
                    models.FileField(blank=True, default=None, null=True, upload_to=''),
                ),
                (
                    'created',
                    models.DateTimeField(
                        help_text='The zip file export, deleted 1 hour after creation'
                    ),
                ),
                (
                    'name',
                    models.CharField(
                        blank=True,
                        help_text='Name of the model run for download',
                        max_length=1024,
                    ),
                ),
                (
                    'celery_id',
                    models.CharField(
                        blank=True, help_text='Celery Task Id', max_length=255
                    ),
                ),
                ('site_evaluation', models.CharField(max_length=255)),
                ('arguments', models.JSONField(default=None, null=True)),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
