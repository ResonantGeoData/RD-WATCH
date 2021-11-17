from datetime import datetime
import json

from celery import shared_task
from django.contrib.gis.geos import Polygon
from django.db import transaction
import pystac
from rgd.tasks.helpers import _run_with_failure_reason


@transaction.atomic
def _process_stac_file(pk):
    from watch.core.models import STACFile
    from watch.core.serializers import ItemSerializer

    stac_file = STACFile.objects.get(pk=pk)

    with stac_file.file.yield_local_path() as path:
        with open(path, 'r') as f:
            data = json.loads(f.read())

    raster_meta = ItemSerializer().create(data)

    # Make sure the file collections match
    images = raster_meta.parent_raster.image_set.images.all()
    for image in images:
        image.file.collection = stac_file.file.collection
        image.file.save(
            update_fields=[
                'collection',
            ]
        )
    for afile in raster_meta.parent_raster.ancillary_files.all():
        afile.collection = stac_file.file.collection
        afile.save(
            update_fields=[
                'collection',
            ]
        )

    stac_file.raster = raster_meta.parent_raster
    stac_file.processed = datetime.now()
    stac_file.save(
        update_fields=[
            'processed',
            'raster',
        ]
    )


@shared_task(time_limit=86400)
def task_ingest_stac_file(pk):
    from watch.core.models import STACFile

    stac_file = STACFile.objects.get(pk=pk)
    _run_with_failure_reason(stac_file, _process_stac_file, pk)


@transaction.atomic
def populate_stac_file_outline(pk):
    from watch.core.models import STACFile

    stac_file = STACFile.objects.get(pk=pk)

    with stac_file.file.yield_local_path() as path:
        with open(path, 'r') as f:
            data = json.loads(f.read())

    # Load with pystac
    item = pystac.Item.from_dict(data)

    # Get bounds
    outline = Polygon(
        (
            [item.bbox[0], item.bbox[1]],
            [item.bbox[0], item.bbox[3]],
            [item.bbox[2], item.bbox[3]],
            [item.bbox[2], item.bbox[1]],
            [item.bbox[0], item.bbox[1]],
        )
    )

    # Populate
    stac_file.outline = outline
    stac_file.save(update_fields=['outline'])


@shared_task(time_limit=86400)
def task_populate_stac_file_outline(pk):
    populate_stac_file_outline(pk)


@shared_task(time_limit=86400)
def task_load_google_cloud_record(record_pk):
    from watch.core.models import GoogleCloudRecord
    from watch.core.tasks.ingest import load_google_cloud_record

    record = GoogleCloudRecord.objects.get(pk=record_pk)
    _run_with_failure_reason(record, load_google_cloud_record, record_pk)
