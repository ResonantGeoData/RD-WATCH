# Generated by Django 5.0.3 on 2024-09-04 06:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0033_remove_region_unique_region_with_owner_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotationexport',
            name='export_file',
            field=models.FileField(blank=True, default=None, null=True, upload_to=''),
        ),
        migrations.CreateModel(
            name='AnimationModelRunExport',
            fields=[
                (
                    'id',
                    models.AutoField(
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
                ('arguments', models.JSONField(default=None, null=True)),
                (
                    'configuration',
                    models.ForeignKey(
                        help_text='ModelRun for Animation export',
                        on_delete=django.db.models.deletion.PROTECT,
                        to='core.modelrun',
                    ),
                ),
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
                    models.AutoField(
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
                ('arguments', models.JSONField(default=None, null=True)),
                (
                    'site_evaluation',
                    models.ForeignKey(
                        help_text='SiteEvaluation for Animation export',
                        on_delete=django.db.models.deletion.PROTECT,
                        to='core.siteevaluation',
                    ),
                ),
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
