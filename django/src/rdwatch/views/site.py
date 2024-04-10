from ninja import Router, Schema
from pydantic import UUID4

from django.db.models import Case, Count, Exists, F, OuterRef, When
from django.db.models.functions import JSONObject
from django.http import HttpRequest

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SatelliteFetching, SiteEvaluation

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


def get_site(site_id: UUID4):
    return (
        SiteEvaluation.objects.select_related('siteimage', 'satellite_fetching')
        .filter(pk=site_id)
        .annotate(
            siteimage_count=Count('siteimage'),
            S2=Count(Case(When(siteimage__source='S2', then=1))),
            WV=Count(Case(When(siteimage__source='WV', then=1))),
            L8=Count(Case(When(siteimage__source='L8', then=1))),
            PL=Count(Case(When(siteimage__source='PL', then=1))),
            time=ExtractEpoch('timestamp'),
            site_id=F('id'),
            downloading=Exists(
                SatelliteFetching.objects.filter(
                    site=OuterRef('pk'),
                    status=SatelliteFetching.Status.RUNNING,
                )
            ),
        )
        .aggregate(
            site=JSONObject(
                id='pk',
                timestamp='time',
                number='number',
                bbox=BoundingBox('geom'),
                images='siteimage_count',
                S2='S2',
                WV='WV',
                L8='L8',
                start_date=ExtractEpoch('start_date'),
                end_date=ExtractEpoch('end_date'),
                status='status',
                filename='cache_originator_file',
                downloading='downloading',
            ),
        ),
    )


@router.get('/{id}')
def getSite(request: HttpRequest, id: UUID4):
    # TODO: Make this properly error if there are issues in getting the information
    return get_site(id)[0]['site']


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
