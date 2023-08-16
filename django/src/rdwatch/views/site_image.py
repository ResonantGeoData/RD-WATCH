from ninja import Router, Schema

from django.contrib.gis.db.models.functions import Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.files.storage import default_storage
from django.db.models import Count
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest
from rest_framework.exceptions import NotFound

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SiteEvaluation, SiteImage, SiteObservation
from rdwatch.schemas.common import BoundingBoxSchema

router = Router()


class SiteImageSchema(Schema):
    timestamp: int  # type: ignore
    source: str
    cloudcover: float
    image: str
    siteobs_id: int | None
    percent_black: float
    bbox: BoundingBoxSchema
    image_dimensions: list[int]
    aws_location: str


class SiteImageListSchema(Schema):
    count: int
    results: list[SiteImageSchema]


class SiteObsGeomSchema(Schema):
    timestamp: int
    geoJSON: dict  # TODO: Replace with pydantics geoJSON
    label: str


class SiteImageResponse(Schema):
    images: SiteImageListSchema
    geoJSON: list[SiteObsGeomSchema]


@router.get('/{id}/', response=SiteImageResponse)
def site_images(request: HttpRequest, id: int):
    if not SiteEvaluation.objects.filter(pk=id).exists():
        raise NotFound()
    image_queryset = (
        SiteImage.objects.filter(siteeval__id=id)
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
        .filter(siteeval__id=id)
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
    # lets get the presigned URL for each image
    for image in image_queryset['results']:
        image['image'] = default_storage.url(image['image'])
    output['images'] = image_queryset
    output['geoJSON'] = geom_queryset['results']

    return output
