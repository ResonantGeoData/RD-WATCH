import json
import tempfile
from datetime import datetime

from ninja import Router
from pydantic import UUID4

from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.core.models import SiteEvaluation, SiteEvaluationTracking, lookups
from rdwatch.core.schemas import SiteEvaluationRequest
from rdwatch.core.tasks import get_site_model_feature_JSON

router = Router()


@router.patch('/{id}/')
def patch_site_evaluation(request: HttpRequest, id: UUID4, data: SiteEvaluationRequest):
    with transaction.atomic():
        site_evaluation = get_object_or_404(
            SiteEvaluation.objects.select_for_update(), pk=id
        )
        old_geom = None
        old_point = None
        if data.geom:
            if data.geom.get('type', False) == 'Point':
                old_point = site_evaluation.point
                site_evaluation.point = GEOSGeometry(json.dumps(data.geom))
            if data.geom.get('type', False) == 'Polygon':
                old_geom = site_evaluation.geom
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
            point=old_point,
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
