from datetime import datetime
import json

from celery import shared_task
from django.db import transaction
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
