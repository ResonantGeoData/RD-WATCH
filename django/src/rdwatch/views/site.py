from ninja import Router, Schema
from pydantic import UUID4

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models import SiteEvaluation

router = Router()


class SiteImageSiteDetailResponse(Schema):
    region_name: str
    configuration_id: str | int  # some values still ints in my case
    number: str
    version: str
    title: str
    performer: str | None
    timemin: int | None
    timemax: int | None

    @staticmethod
    def resolve_region_name(obj: SiteEvaluation) -> str:
        return obj.region.name

    @staticmethod
    def resolve_title(obj: SiteEvaluation) -> str:
        return obj.configuration.title

    @staticmethod
    def resolve_performer(obj: SiteEvaluation) -> str:
        return obj.configuration.performer.slug

    @staticmethod
    def resolve_timemin(obj: SiteEvaluation) -> int | None:
        if obj.start_date:
            return obj.start_date.timestamp()
        return None

    @staticmethod
    def resolve_timemax(obj: SiteEvaluation) -> int | None:
        if obj.end_date:
            return obj.end_date.timestamp()
        return None


@router.get('/{id}/details', response=SiteImageSiteDetailResponse)
def siteDetails(request: HttpRequest, id: UUID4):
    return get_object_or_404(
        SiteEvaluation.objects.select_related(
            'configuration', 'configuration__performer', 'region'
        ),
        id=id,
    )
