from django.contrib.gis.db.models.functions import Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import Count
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SiteEvaluation, SiteImage, SiteObservation
from rdwatch.serializers import (
    SiteImageListSerializer,
    SiteObservationGeomListSerializer,
)


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
                    image_dimensions='image_dimensions',
                    aws_location='aws_location',
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
