import logging

from ninja import Router
from pydantic import UUID4

from django.contrib.gis.db.models import GeometryField
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.files.storage import default_storage
from django.db.models import Count, F, Func, Value
from django.db.models.functions import JSONObject
from django.http import HttpRequest

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.views.site_image import SiteImageResponse
from rdwatch_scoring.models import Observation, Site, SiteImage

logger = logging.getLogger(__name__)


router = Router()


@router.get('/{id}/', response=SiteImageResponse)
def site_images(request: HttpRequest, id: UUID4):
    image_queryset = (
        SiteImage.objects.filter(site=id)
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
                    observation_id='observation',
                    bbox=BoundingBox('image_bbox'),
                    image_dimensions='image_dimensions',
                    aws_location='aws_location',
                )
            ),
        )
    )
    # Get the unique geoJSON shapes for site observations
    geom_queryset = (
        Observation.objects.values('date', 'geometry')
        .order_by('date')
        .filter(site_uuid=id)
        .aggregate(
            results=JSONBAgg(
                JSONObject(
                    label='phase',
                    timestamp=ExtractEpoch('date'),
                    geoJSON=Func(
                        F('geometry'),
                        4326,
                        function='ST_GeomFromText',
                        output_field=GeometryField(),
                    ),
                    bbox=BoundingBox(
                        Func(
                            F('geometry'),
                            4326,
                            function='ST_GeomFromText',
                            output_field=GeometryField(),
                        )
                    ),
                )
            )
        )
    )
    site_eval_data = (
        Site.objects.filter(pk=id)
        .values()
        .annotate(
            json=JSONObject(
                label=F('predicted_phase'),
                status=F('status_annotated'),
                evaluationGeoJSON=Func(
                    F('union_geometry'),
                    4326,
                    function='ST_GeomFromText',
                    output_field=GeometryField(),
                ),
                evaluationBBox=BoundingBox(
                    Func(
                        F('union_geometry'),
                        4326,
                        function='ST_GeomFromText',
                        output_field=GeometryField(),
                    )
                ),
                notes=Value(''),  # TODO
            )
        )[0]
    )
    # GroundTruth requires BAS search and looking into an array of
    # matching generated SiteIds
    output = {}
    # lets get the presigned URL for each image
    for image in image_queryset['results']:
        image['image'] = default_storage.url(image['image'])
    output['images'] = image_queryset
    output['geoJSON'] = geom_queryset['results']
    output['label'] = site_eval_data['json']['label']
    output['status'] = site_eval_data['json']['status']
    output['notes'] = site_eval_data['json']['notes']
    output['evaluationGeoJSON'] = site_eval_data['json']['evaluationGeoJSON']
    output['evaluationBBox'] = site_eval_data['json']['evaluationBBox']
    return output
