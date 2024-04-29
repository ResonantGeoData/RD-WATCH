import logging

from ninja import Query, Router
from ninja.pagination import LimitOffsetPagination, paginate
from pydantic import UUID4

from django.http import HttpRequest

from rdwatch.models import SatelliteFetching

router = Router()
logger = logging.getLogger(__name__)


@router.get('/running/', response=list[UUID4])
@paginate(LimitOffsetPagination)
def satellite_fetching_running(
    request: HttpRequest, model_runs: list[UUID4] = Query(None)  # noqa: B008
):
    running_sites = SatelliteFetching.objects.filter(
        status=SatelliteFetching.Status.RUNNING
    )
    if model_runs is not None and len(model_runs) > 0:
        running_sites = running_sites.filter(site__configuration__in=model_runs)
    running_site_ids = running_sites.values_list('site_id', flat=True)
    return running_site_ids
