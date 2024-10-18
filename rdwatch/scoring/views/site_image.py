import logging

from ninja import Router
from pydantic import UUID4

from django.contrib.gis.db.models import GeometryField
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.files.storage import default_storage
from django.db.models import Case, CharField, Count, F, Func, Value, When
from django.db.models.functions import JSONObject
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.core.db.functions import BoundingBox, ExtractEpoch
from rdwatch.core.views.site_image import SiteImageResponse
from rdwatch.scoring.models import (
    AnnotationProposalObservation,
    AnnotationProposalSite,
    Observation,
    Site,
    SiteImage,
)

logger = logging.getLogger(__name__)


router = Router()


@router.get('/{id}/', response=SiteImageResponse)
def site_images(request: HttpRequest, id: UUID4):
    try:
        Site.objects.get(pk=id)
        site_db_model = Site
        site_db_model_cols = {
            'geometry': 'union_geometry',
            'status': 'predicted_phase',
            'proposal_status': None,
            'notes': None,
        }
        observations = (
            Observation.objects.values('date', 'geometry')
            .order_by('date')
            .filter(site_uuid=id)
        )
        observation_db_model_cols = {'date': 'date', 'phase': 'phase'}
        proposal = False
    except Site.DoesNotExist:
        get_object_or_404(AnnotationProposalSite, pk=id)
        site_db_model = AnnotationProposalSite
        site_db_model_cols = {
            'geometry': 'geometry',
            'status': 'status',
            'proposal_status': 'proposal_status',
            'notes': 'comments',
        }
        observations = (
            AnnotationProposalObservation.objects.values('observation_date', 'geometry')
            .order_by('observation_date')
            .filter(annotation_proposal_site_uuid=id)
        )
        observation_db_model_cols = {
            'date': 'observation_date',
            'phase': 'current_phase',
        }
        proposal = True

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
                    observation_id=Case(
                        # If this image isn't associated with an observation,
                        # explicitly set the observation_id to None
                        When(
                            observation='',
                            then=None,
                        ),
                        default=F('observation'),
                    ),
                    bbox=BoundingBox('image_bbox'),
                    image_dimensions='image_dimensions',
                    uri_locations='uri_locations',
                ),
                default=[],
            ),
        )
    )
    # Get the unique geoJSON shapes for site observations
    geom_queryset = observations.aggregate(
        results=JSONBAgg(
            JSONObject(
                label=Func(
                    F(observation_db_model_cols['phase']),
                    Value(', '),
                    function='array_to_string',
                    output=CharField(),
                )
                if proposal
                else observation_db_model_cols['phase'],
                timestamp=ExtractEpoch(observation_db_model_cols['date']),
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
            ),
            default=[],
        )
    )
    site_eval_data = (
        site_db_model.objects.filter(pk=id)
        .values()
        .annotate(
            json=JSONObject(
                label=F(site_db_model_cols['status']),
                status=F(site_db_model_cols['proposal_status'])
                if site_db_model_cols['proposal_status']
                else Value(''),
                evaluationGeoJSON=Func(
                    F(site_db_model_cols['geometry']),
                    4326,
                    function='ST_GeomFromText',
                    output_field=GeometryField(),
                ),
                evaluationBBox=BoundingBox(
                    Func(
                        F(site_db_model_cols['geometry']),
                        4326,
                        function='ST_GeomFromText',
                        output_field=GeometryField(),
                    )
                ),
                notes=F(site_db_model_cols['notes'])
                if site_db_model_cols['notes']
                else Value(''),  # TODO
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
