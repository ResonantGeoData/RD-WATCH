from ninja import Router, Schema
from pydantic import UUID4

from django.contrib.gis.db.models.functions import Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.files.storage import default_storage
from django.db.models import Count, F
from django.db.models.functions import JSONObject  # type: ignore
from django.http import Http404, HttpRequest

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SiteEvaluation, SiteImage, SiteObservation
from rdwatch.schemas.common import BoundingBoxSchema, TimeRangeSchema

router = Router()


class SiteImageSchema(Schema):
    timestamp: int  # type: ignore
    source: str
    cloudcover: float
    image: str
    siteobs_id: str | None
    percent_black: float
    bbox: BoundingBoxSchema
    image_dimensions: list[int]
    aws_location: str


class SiteImageListSchema(Schema):
    count: int
    results: list[SiteImageSchema]


class SiteObsGeomSchema(Schema):
    timestamp: int | None
    geoJSON: dict  # TODO: Replace with pydantics geoJSON
    label: str


class GroundTruthSchema(Schema):
    timerange: TimeRangeSchema | None = None
    geoJSON: dict
    label: str


class SiteImageResponse(Schema):
    images: SiteImageListSchema
    geoJSON: list[SiteObsGeomSchema]
    evaluationGeoJSON: dict
    status: str | None
    label: str
    notes: str | None
    groundTruth: GroundTruthSchema | None


@router.get('/{id}/', response=SiteImageResponse)
def site_images(request: HttpRequest, id: UUID4):
    if not SiteEvaluation.objects.filter(pk=id).exists():
        raise Http404()
    else:
        site_eval_obj = SiteEvaluation.objects.get(pk=id)
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
    site_eval_data = (
        SiteEvaluation.objects.filter(pk=id)
        .values()
        .annotate(
            json=JSONObject(
                label=F('label__slug'),
                status=F('status'),
                evaluationGeoJSON=Transform('geom', srid=4326),
                notes=F('notes'),
            )
        )[0]
    )
    # get the same Region_#### for ground truth if it exists
    ground_truth = (
        SiteEvaluation.objects.filter(
            region=site_eval_obj.region,
            number=site_eval_obj.number,
            configuration__performer__slug='TE',
            score=1,
        )
        .values()
        .annotate(
            json=JSONObject(
                label=F('label__slug'),
                timerange=JSONObject(
                    min=ExtractEpoch('start_date'),
                    max=ExtractEpoch('end_date'),
                ),
                geoJSON=Transform('geom', srid=4326),
            )
        )
    )
    output = {}
    # lets get the presigned URL for each image
    for image in image_queryset['results']:
        image['image'] = default_storage.url(image['image'])
    output['images'] = image_queryset
    output['geoJSON'] = geom_queryset['results']
    output['label'] = site_eval_data['json']['label']
    output['status'] = site_eval_data['json']['status']
    output['notes'] = site_eval_data['json']['notes']
    if ground_truth.exists():
        output['groundTruth'] = ground_truth[0]['json']
    output['evaluationGeoJSON'] = site_eval_data['json']['evaluationGeoJSON']
    return output
