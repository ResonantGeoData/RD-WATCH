import logging

from ninja import Query, Router
from pydantic import UUID4

from django.http import HttpRequest

from rdwatch_scoring.models import SatelliteFetching

router = Router()
logger = logging.getLogger(__name__)


@router.get('/running/')
def satellite_fetching_running(
    request: HttpRequest, model_runs: list[UUID4] = Query(None)  # noqa: B008
):
    running_sites = SatelliteFetching.objects.filter(
        status=SatelliteFetching.Status.RUNNING
    )
    if model_runs is not None and len(model_runs) > 0:
        running_sites = running_sites.filter(model_run_uuid__in=model_runs)
    running_site_ids = list(running_sites.values_list('site', flat=True))
    return running_site_ids
