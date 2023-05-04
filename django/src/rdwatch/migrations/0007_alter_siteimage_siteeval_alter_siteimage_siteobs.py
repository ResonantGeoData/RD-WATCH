# Generated by Django 4.1.9 on 2023-05-04 10:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0006_siteimage_siteimage_rdwatch_sit_timesta_808546_gist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteimage',
            name='siteeval',
            field=models.ForeignKey(
                help_text='The site evaluation associated with this observation.',
                on_delete=django.db.models.deletion.CASCADE,
                to='rdwatch.siteevaluation',
            ),
        ),
        migrations.AlterField(
            model_name='siteimage',
            name='siteobs',
            field=models.ForeignKey(
                help_text='The site Observation associated\
                    with this Image if it exists.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='rdwatch.siteobservation',
            ),
        ),
    ]
