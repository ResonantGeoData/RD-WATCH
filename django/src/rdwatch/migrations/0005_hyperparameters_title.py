# Generated by Django 4.1 on 2022-12-14 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rdwatch", "0004_remove_siteobservation_uniq_siteobv_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="hyperparameters",
            name="title",
            field=models.CharField(default="", max_length=1000),
            preserve_default=False,
        ),
    ]
