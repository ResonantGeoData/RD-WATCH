import logging

from celery.result import AsyncResult
from ninja import Query, Router
from pydantic import UUID4

from django.http import HttpRequest

from rdwatch.core.views.satellite_fetching import RunningSatelliteFetchingSchema
from rdwatch.scoring.models import SatelliteFetching

router = Router()
logger = logging.getLogger(__name__)


@router.get('/running/', response=RunningSatelliteFetchingSchema)
def satellite_fetching_running(
    request: HttpRequest, model_runs: list[UUID4] = Query(None)  # noqa: B008
):
    running_sites = SatelliteFetching.objects.filter(
        status=SatelliteFetching.Status.RUNNING
    )
    if model_runs is not None and len(model_runs) > 0:
        running_sites = running_sites.filter(model_run_uuid__in=model_runs)
    running_site_ids = list(running_sites.values('site', 'celery_id'))
    results = []
    for item in running_site_ids:
        task = AsyncResult(item['celery_id'])
        error = item['error']
        if isinstance(task.info, Exception):
            error = str(task.info)
        else:
            task_info = task.info
        site_id = item['site_id']
        results.append({'siteId': site_id, 'info': task_info, 'error': error})

    return {'items': results, 'count': len(running_site_ids)}
