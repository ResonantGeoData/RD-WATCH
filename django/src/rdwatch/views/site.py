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
from rdwatch.models import SiteEvaluation
from ninja import Router, Schema

router = Router()

class SiteImageSiteDetailResponse(Schema):
    regionName: str
    configurationId: str | int # some values still ints in my case
    siteNumber: str
    version: str
    title: str
    performer: str | None
    timemin: int | None
    timemax: int | None


@router.get('/{id}/details', response=SiteImageSiteDetailResponse)
def siteDetails(request: HttpRequest, id: UUID4):
    return SiteEvaluation.objects.filter(pk=id).annotate(
        configurationId=F('configuration'),
        title=F('configuration__title'),
        timemin=ExtractEpoch('start_date'),
        timemax=ExtractEpoch('end_date'),
        regionName=F('region__name'),
        performer=F('configuration__performer__slug'),
        siteNumber=F('number')
    ).first()
