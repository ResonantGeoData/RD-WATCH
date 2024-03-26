from ninja import Router, Schema
from pydantic import UUID4

from django.db.models import F
from django.http import HttpRequest

from rdwatch.db.functions import ExtractEpoch
from rdwatch.models import SiteEvaluation

router = Router()


class SiteImageSiteDetailResponse(Schema):
    regionName: str
    configurationId: str | int  # some values still ints in my case
    siteNumber: str
    version: str
    title: str
    performer: str | None
    timemin: int | None
    timemax: int | None


@router.get('/{id}/details/', response=SiteImageSiteDetailResponse)
def siteDetails(request: HttpRequest, id: UUID4):
    return (
        SiteEvaluation.objects.filter(pk=id)
        .annotate(
            configurationId=F('configuration'),
            title=F('configuration__title'),
            timemin=ExtractEpoch('start_date'),
            timemax=ExtractEpoch('end_date'),
            regionName=F('region__name'),
            performer=F('configuration__performer__slug'),
            siteNumber=F('number'),
        )
        .first()
    )
