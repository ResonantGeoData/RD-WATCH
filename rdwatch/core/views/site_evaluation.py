import json
import tempfile
from datetime import datetime
from typing import Literal

from ninja import Router, Schema
from pydantic import UUID4

from django.contrib.gis.db.models.functions import Transform
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.core.models import SiteEvaluation, SiteEvaluationTracking, lookups
from rdwatch.core.schemas import SiteEvaluationRequest
from rdwatch.core.tasks.animation_export import create_animation

router = Router()


@router.patch('/{id}/')
def patch_site_evaluation(request: HttpRequest, id: UUID4, data: SiteEvaluationRequest):
    with transaction.atomic():
        site_evaluation = get_object_or_404(
            SiteEvaluation.objects.select_for_update(), pk=id
        )
        old_geom = None
        if data.geom:
            old_geom = site_evaluation.geom  # if geom is modified, backup
            site_evaluation.geom = GEOSGeometry(json.dumps(data.geom))
        SiteEvaluationTracking.objects.create(
            score=site_evaluation.score,
            label=site_evaluation.label,
            end_date=site_evaluation.end_date,
            start_date=site_evaluation.start_date,
            notes=site_evaluation.notes,
            edited=datetime.now(),
            evaluation=site_evaluation,
            geom=old_geom,
        )
        if data.label:
            site_evaluation.label = lookups.ObservationLabel.objects.get(
                slug=data.label
            )

        # Use `exclude_unset` here because an explicitly `null` start/end date
        # means something different than a missing start/end date.
        data_dict = data.dict(exclude_unset=True)

        FIELDS = ('start_date', 'end_date', 'notes', 'status')
        for field in filter(lambda f: f in data_dict, FIELDS):
            setattr(site_evaluation, field, data_dict[field])

        site_evaluation.modified_timestamp = datetime.now()
        site_evaluation.save()

    return 200


def get_site_model_feature_JSON(id: UUID4, obsevations=False):
    query = (
        SiteEvaluation.objects.filter(pk=id)
        .values()
        .annotate(
            json=JSONObject(
                site=JSONObject(
                    region='configuration__region__name',
                    number='number',
                ),
                configuration='configuration__parameters',
                version='version',
                performer=JSONObject(
                    id='configuration__performer__id',
                    team_name='configuration__performer__team_name',
                    short_code='configuration__performer__short_code',
                ),
                cache_originator_file='cache_originator_file',
                cache_timestamp='cache_timestamp',
                cache_commit_hash='cache_commit_hash',
                notes='notes',
                score='score',
                status='label__slug',
                geom=Transform('geom', srid=4326),
                start_date=('start_date'),
                end_date=('end_date'),
            )
        )
    )
    if query.exists():
        data = query[0]['json']

        region_name = data['site']['region']
        site_id = f'{region_name}_{str(data["site"]["number"]).zfill(4)}'
        version = data['version']
        output = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': {
                        'type': 'site',
                        'region_id': region_name,
                        'site_id': site_id,
                        'version': version,
                        'status': data['status'],
                        'score': data['score'],
                        'start_date': (
                            None
                            if data['start_date'] is None
                            else datetime.fromisoformat(data['start_date']).strftime(
                                '%Y-%m-%d'
                            )
                        ),
                        'end_date': (
                            None
                            if data['end_date'] is None
                            else datetime.fromisoformat(data['end_date']).strftime(
                                '%Y-%m-%d'
                            )
                        ),
                        'model_content': 'annotation',
                        'originator': data['performer']['short_code'],
                    },
                    'geometry': data['geom'],
                }
            ],
        }
        filename = None
        if data['cache_originator_file']:
            filename = data['cache_originator_file']
            output['features'][0]['properties']['cache'] = {
                'cache_originator_file': data['cache_originator_file'],
                'cache_timestamp': data['cache_timestamp'],
                'cache_commit_hash': data['cache_commit_hash'],
                'cache_notes': data['notes'],
            }
        return output, site_id, filename
    return None, None


@router.get('/{id}/download/')
def download_annotations(request: HttpRequest, id: UUID4):
    output, site_id, filename = get_site_model_feature_JSON(id)
    if output is not None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            json_data = json.dumps(output).encode('utf-8')
            temp_file.write(json_data)

        # Return the temporary file for download
        with open(temp_file.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename={site_id}.geojson'

            return response
    # TODO: Some Better Error response
    return 500, 'Unable to export data'


class GenerateAnimationSchema(Schema):
    output_format: Literal['mp4', 'gif'] = 'mp4'
    fps: float = 1
    point_radius: int = 5
    sources: list[Literal['WV', 'S2', 'L8', 'PL']] = ['WV', 'S2', 'L8', 'PL']
    labels: list[Literal['geom', 'date', 'source', 'obs', 'obs_label']] = [
        'geom',
        'date',
        'source',
        'obs',
        'obs_label',
    ]
    rescale: bool = False
    rescale_border: float = 1.0


@router.post('/{id}/animation')
def generate_animation(
    request: HttpRequest,
    id: UUID4,
    params: GenerateAnimationSchema,  # noqa: B008
):
    # Fetch the SiteEvaluation instance
    datapath = create_animation(
        site_evaluation_id=id,
        output_format=params.output_format,
        fps=params.fps,
        point_radius=params.point_radius,
        sources=params.sources,
        labels=params.labels,
        rescale=params.rescale,
        rescale_border=params.rescale_border,
    )
    if datapath:
        with open(datapath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            output_format = params.output_format
            response[
                'Content-Disposition'
            ] = f'attachment; filename={id}.{output_format}'
            return response
    return 500, 'Unable to export data'
