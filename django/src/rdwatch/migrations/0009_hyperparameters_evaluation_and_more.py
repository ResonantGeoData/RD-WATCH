# Generated by Django 4.1.9 on 2023-06-12 07:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0008_satellitefetching_celery_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='hyperparameters',
            name='evaluation',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hyperparameters',
            name='evaluation_run',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='siteevaluation',
            name='version',
            field=models.CharField(
                blank=True,
                help_text='Version of annotations',
                max_length=255,
                null=True,
            ),
        ),
    ]
