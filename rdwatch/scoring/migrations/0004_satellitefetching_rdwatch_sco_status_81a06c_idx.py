# Generated by Django 5.0.3 on 2024-04-24 13:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('scoring', '0003_siteimage_image_embedding'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='satellitefetching',
            index=models.Index(fields=['status'], name='rdwatch_sco_status_81a06c_idx'),
        ),
    ]
