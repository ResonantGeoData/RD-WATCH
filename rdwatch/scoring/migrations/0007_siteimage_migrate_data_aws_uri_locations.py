# Generated by Django 5.0.9 on 2024-10-16 15:20

from django.db import migrations


def migrate_aws_location_to_uri_locations(apps, schema_editor):
    SiteImage = apps.get_model('scoring', 'SiteImage')
    dbalias = schema_editor.connection.alias
    for site_image in SiteImage.objects.using(dbalias).all():
        if site_image.aws_location:
            site_image.uri_locations = [site_image.aws_location]
        site_image.save(using=dbalias)


def reverse_migrate_aws_location_to_uri_locations(apps, schema_editor):
    SiteImage = apps.get_model('scoring', 'SiteImage')
    dbalias = schema_editor.connection.alias
    for site_image in SiteImage.objects.using(dbalias).all():
        if site_image.uri_locations:
            # pick the first URI
            site_image.aws_location = site_image.uri_locations[0]
        else:
            site_image.aws_location = ''
        site_image.save(using=dbalias)


class Migration(migrations.Migration):
    dependencies = [
        ('scoring', '0006_siteimage_uri_locations'),
    ]

    operations = [
        migrations.RunPython(
            migrate_aws_location_to_uri_locations,
            reverse_migrate_aws_location_to_uri_locations,
        ),
    ]
