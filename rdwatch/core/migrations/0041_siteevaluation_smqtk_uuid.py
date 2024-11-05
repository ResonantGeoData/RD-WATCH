# Generated by Django 5.0.9 on 2024-10-25 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_remove_siteimage_aws_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteevaluation',
            name='smqtk_uuid',
            field=models.CharField(blank=True, help_text='SMQTK UUID', max_length=256, null=True),
        ),
    ]
