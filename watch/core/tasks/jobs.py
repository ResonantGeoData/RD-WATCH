from datetime import datetime
import json

from celery import shared_task
from django.db import transaction
from rgd.tasks.helpers import _run_with_failure_reason
from rgd_imagery.serializers.stac import ItemSerializer


@transaction.atomic
def _process_stac_item(pk):
    from watch.core.models import STACItem

    stac_item = STACItem.objects.get(pk=pk)

    with stac_item.item.yield_local_path() as path:
        with open(path, 'r') as f:
            data = json.loads(f.read())

    raster_meta = ItemSerializer().create(data)

    # Make sure the file collections match
    images = raster_meta.parent_raster.image_set.images.all()
    for image in images:
        image.file.collection = stac_item.item.collection
        image.file.save(
            update_fields=[
                'collection',
            ]
        )
    for afile in raster_meta.parent_raster.ancillary_files.all():
        afile.collection = stac_item.item.collection
        afile.save(
            update_fields=[
                'collection',
            ]
        )

    stac_item.raster = raster_meta.parent_raster
    stac_item.processed = datetime.now()
    stac_item.save(
        update_fields=[
            'processed',
            'raster',
        ]
    )


@shared_task(time_limit=86400)
def task_ingest_stac_item(pk):
    from watch.core.models import STACItem

    stac_item = STACItem.objects.get(pk=pk)
    _run_with_failure_reason(stac_item, _process_stac_item, pk)
