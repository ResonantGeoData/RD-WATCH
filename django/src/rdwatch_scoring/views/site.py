from ninja import Router
from pydantic import UUID4

from django.contrib.gis.db.models import GeometryField
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.files.storage import default_storage
from django.db.models import Count, F, Func, Value
from django.db.models.functions import JSONObject
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    ExpressionWrapper,
    F,
    Field,
    Func,
    Min,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
    Window,
)
from django.db.models.functions import Concat, Lower, Replace, Substr

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch_scoring.models import Observation, Site, SiteImage
from ninja import Router, Schema
from rdwatch.views.site import SiteImageSiteDetailResponse
router = Router()




@router.get('/{id}/details', response=SiteImageSiteDetailResponse)
def siteDetails(request: HttpRequest, id: UUID4):
    return Site.objects.filter(pk=id).annotate(
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
    ).first()
