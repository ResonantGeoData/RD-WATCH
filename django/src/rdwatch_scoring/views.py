import logging

from ninja import Schema
from ninja.pagination import RouterPaginated


from rdwatch.models import HyperParameters, Region
from rdwatch.views.region import RegionSchema
from rdwatch.models.lookups import Performer
# Create your views here.
from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponse,
)

from .models import Observation, EvaluationRun, Site, EvaluationActivityClassificationTemporalIou

logger = logging.getLogger(__name__)


router = RouterPaginated()

class TemporalSchema(Schema):
    site_preparation: str = None
    active_construction: str = None
    post_construction: str = None


class ResponseSchema(Schema):
    region_name: str = None
    evaluationId: int = None
    evaluation_run: int = None
    performer: str = None
    evaluation_uuid: str = None
    unionArea: float = None
    statusAnnotated: str = None
    temporalIOU: TemporalSchema = None



@router.get('/', response=ResponseSchema)
def list_regions(request: HttpRequest):
    if (
        'configurationId' not in request.GET
        or 'regionId' not in request.GET
        or 'siteNumber' not in request.GET
        or 'version' not in request.GET
    ):
        return HttpResponseBadRequest()
    configId = request.GET['configurationId']
    regionId = request.GET['regionId']
    siteNumber = request.GET['siteNumber']
    version = request.GET['version']
    # from the hyper parameters we need the evaluation and evaluation_run Ids
    configuration = HyperParameters.objects.filter(pk=configId).first()
    evaluationId = configuration.evaluation
    performer_name = configuration.performer.slug.lower()
    evaluation_run = configuration.evaluation_run
    region_name = RegionSchema.resolve_name(Region.objects.filter(pk=regionId).first())

    evaluation = EvaluationRun.objects.filter(evaluation_run_number=evaluation_run, evaluation_number=evaluationId, region=region_name).first()
    if evaluation:
        evaluationUUID = evaluation.uuid
        # Now we can get the SiteId information for this evaluationId
        generatedSiteId = f'{region_name}_{siteNumber.zfill(4)}_{performer_name}_{version}'
        logger.warning(generatedSiteId)
        siteObj = Site.objects.filter(site_id=generatedSiteId, evaluation_run_uuid=evaluationUUID).first()
        unionArea = siteObj.union_area
        status_annotated = siteObj.status_annotated
        temporalIOU = EvaluationActivityClassificationTemporalIou.objects.filter(site_proposal=generatedSiteId, evaluation_run_uuid=evaluationUUID, activity_type='overall').first()
        if temporalIOU:
            tempDict = {
                'site_preparation': temporalIOU.site_preparation,
                'active_construction': temporalIOU.active_construction,
                'post_construction': temporalIOU.post_construction,
            }
        return {
            'region_name': region_name,
            'evaluationId': evaluationId,
            'evaluation_run': evaluation_run,
            'performer': performer_name,
            'evaluation_uuid': evaluationUUID,
            'unionArea': unionArea,
            'statusAnnotated': status_annotated,
            'temporalIOU': tempDict,
        }
    return HttpResponse('Scoring not Found', status=404)
