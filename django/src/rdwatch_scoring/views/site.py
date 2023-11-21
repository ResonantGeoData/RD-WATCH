from datetime import datetime

from ninja import Router
from pydantic import UUID4

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.views.site_evaluation import SiteDetailResponse as BaseSiteDetailResponse
from rdwatch_scoring.models import Site

router = Router()


class SiteDetailResponse(BaseSiteDetailResponse):
    @staticmethod
    def resolve_configuration_id(obj: Site) -> str:
        return str(obj.evaluation_run_uuid_id)

    @staticmethod
    def resolve_region_name(obj: Site) -> str:
        return obj.region.id

    @staticmethod
    def resolve_title(obj: Site) -> str:
        return ' '.join(
            [
                'Eval',
                str(obj.evaluation_run_uuid.evaluation_number),
                str(obj.evaluation_run_uuid.evaluation_run_number),
                obj.evaluation_run_uuid.performer,
            ]
        )

    @staticmethod
    def resolve_performer(obj: Site) -> str:
        return obj.originator

    @staticmethod
    def resolve_timemin(obj: Site) -> int | None:
        if obj.start_date:
            return datetime.combine(obj.start_date, datetime.min.time()).timestamp()
        return None

    @staticmethod
    def resolve_timemax(obj: Site) -> int | None:
        if obj.end_date:
            return datetime.combine(obj.end_date, datetime.min.time()).timestamp()
        return None

    @staticmethod
    def resolve_number(obj: Site) -> str:
        return obj.site_id[8:]


@router.get('/{id}/', response=SiteDetailResponse)
def get_site(request: HttpRequest, id: UUID4):
    return get_object_or_404(
        Site.objects.select_related('evaluation_run_uuid', 'region'),
        pk=id,
    )
