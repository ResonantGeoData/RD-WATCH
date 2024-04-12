import json
from datetime import datetime

from ninja import Router
from pydantic import UUID4

from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.http import Http404, HttpRequest

from rdwatch.schemas import SiteEvaluationRequest
from rdwatch_scoring.models import AnnotationProposalSiteLog

router = Router()


@router.patch('/{uuid}/')
def update_annotation_proposal_site(
    request: HttpRequest, uuid: UUID4, data: SiteEvaluationRequest
):
    with transaction.atomic():
        proposal_site_update = (
            AnnotationProposalSiteLog.objects.filter(uuid=uuid)
            .order_by('-timestamp')
            .first()
        )

        if not proposal_site_update:
            raise Http404()

        proposal_site_update.serial_id = None
        proposal_site_update.timestamp = datetime.utcnow()

        data_dict = data.dict(exclude_unset=True)

        FIELDS = ('label', 'start_date', 'end_date', 'score', 'status', 'notes', 'geom')
        for field in filter(lambda f: f in data_dict, FIELDS):
            if field == 'geom':
                proposal_site_update['geometry'] = GEOSGeometry(
                    json.dumps(data_dict[field])
                ).wkt
            elif field == 'label':
                proposal_site_update['status'] = data_dict[field]
            elif field == 'status':
                proposal_site_update['proposal_status'] = data_dict[field]
            elif field == 'notes':
                proposal_site_update['comments'] = data_dict[field]
            else:
                proposal_site_update[field] = data_dict[field]

        proposal_site_update.save()

    return 200
