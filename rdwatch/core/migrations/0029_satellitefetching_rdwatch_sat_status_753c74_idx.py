# Generated by Django 5.0.3 on 2024-04-24 13:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0028_remove_siteevaluation_region_alter_modelrun_region'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='satellitefetching',
            index=models.Index(fields=['status'], name='core_satell_status_af6335_idx'),
        ),
    ]
