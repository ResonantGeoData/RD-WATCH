from ninja import Router
from pydantic import UUID4

from django.contrib.gis.db.models import GeometryField
from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import (
    Case,
    CharField,
    Count,
    Exists,
    ExpressionWrapper,
    F,
    Func,
    OuterRef,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, JSONObject, Substr
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.core.db.functions import BoundingBox, ExtractEpoch
from rdwatch.core.views.site import SiteImageSiteDetailResponse
from rdwatch.scoring.models import SatelliteFetching, Site, SiteImage

router = Router()


def get_site_query(site_id: UUID4):
    site_list = Site.objects.filter(pk=site_id).aggregate(
        sites=JSONBAgg(
            JSONObject(
                id='pk',
                number=Substr(F('site_id'), 9, 4),  # pos is 1 indexed,
                bbox=BoundingBox(
                    Func(
                        F('union_geometry'),
                        4326,
                        function='ST_GeomFromText',
                        output_field=GeometryField(),
                    )
                ),
                # images='siteimage_count',
                # S2='S2',
                # WV='WV',
                # L8='L8',
                start_date=Coalesce(
                    ExtractEpoch('start_date'), ExtractEpoch('point_date')
                ),
                end_date=Coalesce(ExtractEpoch('end_date'), ExtractEpoch('point_date')),
                # status='status',
                # filename='cache_originator_file',
                # downloading='downloading',
            ),
            ordering='site_id',
            default=[],
        ),
    )
    image_queryset = (
        SiteImage.objects.filter(site=site_id)
        .values('site')
        .annotate(
            S2=Count(Case(When(source='S2', then=1))),
            WV=Count(Case(When(source='WV', then=1))),
            L8=Count(Case(When(source='L8', then=1))),
            PL=Count(Case(When(source='PL', then=1))),
            downloading=Exists(
                SatelliteFetching.objects.filter(
                    site=OuterRef('site'),
                    status=SatelliteFetching.Status.RUNNING,
                )
            ),
        )
    )

    image_info = {i['site']: i for i in image_queryset}

    for s in site_list['sites']:
        if s['id'] in image_info.keys():
            site_image_info = image_info[s['id']]
        else:
            site_image_info = {'S2': 0, 'WV': 0, 'L8': 0, 'PL': 0, 'downloading': False}

        s['images'] = (
            site_image_info['S2']
            + site_image_info['WV']
            + site_image_info['L8']
            + site_image_info['PL']
        )
        s['S2'] = site_image_info['S2']
        s['WV'] = site_image_info['WV']
        s['L8'] = site_image_info['L8']
        s['PL'] = site_image_info['PL']
        s['downloading'] = site_image_info['downloading']
    return site_list['sites'][0]


@router.get('/{id}')
def get_site(request: HttpRequest, id: UUID4):
    get_object_or_404(Site, pk=id)
    return get_site_query(id)


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
            timemin=Coalesce(ExtractEpoch('start_date'), ExtractEpoch('point_date')),
            timemax=Coalesce(ExtractEpoch('end_date'), ExtractEpoch('point_date')),
            regionName=F('region'),
            performer=F('originator'),
            siteNumber=Substr(F('site_id'), 9),  # pos is 1 indexed
        )
        .first()
    )
