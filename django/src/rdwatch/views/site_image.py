from datetime import datetime

from celery.result import AsyncResult

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.gis.db.models.functions import Area, Transform, AsGeoJSON
from django.contrib.postgres.aggregates import JSONBAgg
from django.db import transaction
from django.db.models import Count, F, Max, Min, RowRange, Window, IntegerField
from django.db.models.functions import JSONObject  # type: ignore
from django.contrib.postgres.aggregates import ArrayAgg
from django.http import HttpRequest
from rest_framework import status
from rest_framework.decorators import api_view, schema
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SatelliteFetching, SiteEvaluation, SiteImage, SiteObservation
from rdwatch.serializers import SiteImageListSerializer, SiteObservationGeomListSerializer
from rdwatch.tasks import get_siteobservations_images


@api_view(['GET'])
def site_images(request: HttpRequest, pk: int):
    if not SiteEvaluation.objects.filter(pk=pk).exists():
        raise NotFound()
    image_queryset = (
        SiteImage.objects.filter(siteeval__id=pk)
        .order_by('timestamp')
        .aggregate(
            count=Count('pk'),
            results=JSONBAgg(
                JSONObject(
                    id='pk',
                    timestamp=ExtractEpoch('timestamp'),
                    image='image',
                    cloudcover='cloudcover',
                    percent_black='percent_black',
                    source='source',
                    siteobs_id='siteobs_id',
                    bbox=BoundingBox('image_bbox'),
                    image_dimensions='image_dimensions'
                )
            ),
        )
    )
    # Get the unique geoJSON shapes for site observations
    geom_queryset = (
        SiteObservation.objects.values('timestamp', 'geom')
            .order_by('timestamp')
            .filter(siteeval__id=pk)
            .aggregate(
                results=JSONBAgg(
                    JSONObject(
                        label='label__slug',
                        timestamp=ExtractEpoch('timestamp'),
                        geoJSON=Transform('geom', srid=4326),
                    )
                )
            )
    )
    output = {}
    image_serializer = SiteImageListSerializer(image_queryset)
    geom_serializer = SiteObservationGeomListSerializer(geom_queryset)
    output['images'] = image_serializer.data
    output['geoJSON'] = geom_serializer.data
    return Response(output)
