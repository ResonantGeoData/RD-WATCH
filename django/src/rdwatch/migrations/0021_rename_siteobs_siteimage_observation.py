# Generated by Django 4.1.9 on 2023-10-26 12:27

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('rdwatch', '0020_alter_siteevaluation_timestamp'),
    ]

    operations = [
        migrations.RenameField(
            model_name='siteimage',
            old_name='siteobs',
            new_name='observation',
        ),
    ]
