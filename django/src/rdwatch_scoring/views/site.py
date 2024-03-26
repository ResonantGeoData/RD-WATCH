from ninja import Router
from pydantic import UUID4

from django.db.models import CharField, ExpressionWrapper, F, Value
from django.db.models.functions import Concat, Substr
from django.http import HttpRequest

from rdwatch.db.functions import ExtractEpoch
from rdwatch.views.site import SiteImageSiteDetailResponse
from rdwatch_scoring.models import Site

router = Router()


@router.get('/{id}/details/', response=SiteImageSiteDetailResponse)
def siteDetails(request: HttpRequest, id: UUID4):
    return (
        Site.objects.filter(pk=id)
        .annotate(
            configurationId=F('evaluation_run_uuid'),
            title=ExpressionWrapper(
                Concat(
                    Value('Eval '),
                    F('evaluation_run_uuid__evaluation_number'),
                    Value(' '),
                    F('evaluation_run_uuid__evaluation_run_number'),
                    Value(' '),
                    F('evaluation_run_uuid__performer'),
                ),
                output_field=CharField(),
            ),
            timemin=ExtractEpoch('start_date'),
            timemax=ExtractEpoch('end_date'),
            regionName=F('region'),
            performer=F('originator'),
            siteNumber=Substr(F('site_id'), 9),  # pos is 1 indexed
        )
        .first()
    )
