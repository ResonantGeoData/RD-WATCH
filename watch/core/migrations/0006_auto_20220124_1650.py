# Generated by Django 3.2.11 on 2022-01-24 16:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_stacfile_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='region',
            name='spatialentry_ptr',
        ),
        migrations.DeleteModel(
            name='Feature',
        ),
        migrations.DeleteModel(
            name='Region',
        ),
    ]
