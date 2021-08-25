from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_load_region_landsat(region_pk):
    from watch.core.models import Region
    from watch.core.tasks.watch_gc_ls import load_region_landsat

    region = Region.objects.get(pk=region_pk)
    helpers._run_with_failure_reason(region, load_region_landsat, region_pk)
