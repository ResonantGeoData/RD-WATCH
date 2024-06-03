from celery.result import AsyncResult
from ninja import Router, Schema
from pydantic import UUID4

from django.contrib.gis.db.models.functions import Transform
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.files.storage import default_storage
from django.db.models import Count, F
from django.db.models.functions import JSONObject  # type: ignore
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.core.db.functions import BoundingBox, ExtractEpoch
from rdwatch.core.models import SiteEvaluation, SiteImage, SiteObservation
from rdwatch.core.schemas.common import BoundingBoxSchema, TimeRangeSchema
from rdwatch.core.tasks import generate_image_embedding

router = Router()


class SiteImageSchema(Schema):
    timestamp: int
    source: str
    cloudcover: float | None
    image: str
    observation_id: UUID4 | None
    percent_black: float | None
    bbox: BoundingBoxSchema
    image_dimensions: list[int]
    aws_location: str
    image_embedding: str | None
    id: int


class SiteImageListSchema(Schema):
    count: int
    results: list[SiteImageSchema]


class SiteObsGeomSchema(Schema):
    timestamp: int | None
    geoJSON: dict  # TODO: Replace with pydantics geoJSON
    bbox: dict
    label: str | None


class GroundTruthSchema(Schema):
    timerange: TimeRangeSchema | None = None
    geoJSON: dict
    label: str | None


class SiteImageResponse(Schema):
    images: SiteImageListSchema
    geoJSON: list[SiteObsGeomSchema]
    evaluationGeoJSON: dict
    evaluationBBox: dict
    status: str | None
    label: str | None
    notes: str | None
    groundTruth: GroundTruthSchema | None


@router.get('/{id}/', response=SiteImageResponse)
def site_images(request: HttpRequest, id: UUID4):
    site_eval_obj = get_object_or_404(
        SiteEvaluation.objects.select_related('configuration'), pk=id
    )

    image_queryset = (
        SiteImage.objects.filter(site__id=id)
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
                    observation_id='observation_id',
                    bbox=BoundingBox('image_bbox'),
                    image_dimensions='image_dimensions',
                    aws_location='aws_location',
                    image_embedding='image_embedding',
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
                    label=F('label__slug'),
                    timestamp=ExtractEpoch('timestamp'),
                    geoJSON=Transform('geom', srid=4326),
                    bbox=BoundingBox(Transform('geom', srid=4326)),
                ),
                default=[],
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
                evaluationBBox=BoundingBox(Transform('geom', srid=4326)),
                notes=F('notes'),
            )
        )[0]
    )
    # get the same Region_#### for ground truth if it exists
    ground_truth = (
        SiteEvaluation.objects.filter(
            configuration__region=site_eval_obj.configuration.region,
            number=site_eval_obj.number,
            configuration__performer__short_code='TE',
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
    output['evaluationBBox'] = site_eval_data['json']['evaluationBBox']
    return output


@router.post('/{id}/image_embedding/', response=UUID4)
def post_image_embedding(request: HttpRequest, id: int):
    get_object_or_404(SiteImage, pk=id)
    return generate_image_embedding.delay(id).id


@router.get('/{id}/image_embedding_status/{uuid}/')
def get_image_embedding_status(request: HttpRequest, id: int, uuid: UUID4):
    get_object_or_404(SiteImage, pk=id)
    task = AsyncResult(uuid)
    result = {
        'state': task.state,
        'status': task.status,
    }
    return result


@router.get('/{id}/image/', response=SiteImageSchema)
def get_site_image(request: HttpRequest, id: int):
    site_image = (
        SiteImage.objects.filter(pk=id)
        .annotate(
            timestamp_epoch=ExtractEpoch('timestamp'),
            bbox=BoundingBox('image_bbox'),
        )
        .values(
            'timestamp_epoch',
            'source',
            'cloudcover',
            'image',
            'observation_id',
            'bbox',
            'percent_black',
            'image_dimensions',
            'aws_location',
            'image_embedding',
            'pk',  # Assuming 'pk' is the primary key field name
        )
        .first()
    )
    if site_image:
        response_data = {
            'timestamp': site_image['timestamp_epoch'],
            'source': site_image['source'],
            'cloudcover': site_image['cloudcover'],
            'image': default_storage.url(site_image['image']),
            'observation_id': site_image['observation_id'],
            'percent_black': site_image['percent_black'],
            'bbox': site_image['bbox'],
            'image_dimensions': site_image['image_dimensions'],
            'aws_location': site_image['aws_location'],
            'image_embedding': default_storage.url(site_image['image_embedding']),
            'id': site_image['pk'],
        }
        return response_data
    else:
        raise Http404()
