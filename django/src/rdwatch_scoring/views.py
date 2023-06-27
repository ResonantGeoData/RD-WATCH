import logging

from ninja import Schema
from ninja.pagination import RouterPaginated

# Create your views here.
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest

from rdwatch.models import HyperParameters, Region
from rdwatch.views.region import RegionSchema

from .models import (
    EvaluationActivityClassificationTemporalIou,
    EvaluationBroadAreaSearchDetection,
    EvaluationRun,
    Site,
)

logger = logging.getLogger(__name__)


router = RouterPaginated()


# Query for the Scoring Database to get unique truth typs based on the parmeters
def get_unique_site_truth_types(evaluation_run_uid, activity_type, generatedSiteId):
    site_proposals = EvaluationBroadAreaSearchDetection.objects.filter(
        evaluation_run_uuid=evaluation_run_uid,
        activity_type=activity_type,
        site_proposal_matched__contains=generatedSiteId,
    ).distinct()

    # Retrieve unique site_truth_type values from the filtered site proposals
    unique_site_truth_types = site_proposals.values_list(
        'site_truth_type', flat=True
    ).distinct()

    return list(unique_site_truth_types)


# Gets coloring for sites based on their scoring results
def get_site_scoring_color(evaluation_run_uid, activity_type, generatedSiteId):
    match_statuses = get_unique_site_truth_types(
        evaluation_run_uid, activity_type, generatedSiteId
    )
    sm_color = 'magenta'
    if len(match_statuses):
        if set(match_statuses) & {
            'positive_annotated',
            'positive_annotated_static',
            'positive_partial',
            'positive_pending',
        }:
            # and at least 1 negative match (partially wrong)
            if set(match_statuses) & {
                'positive_excluded',
                'negative',
                'negative_unbounded',
            }:
                sm_color = 'orange'
            else:
                sm_color = '#66CCAA'
        # only negative matches (completely wrong)
        elif set(match_statuses) & {
            'positive_excluded',
            'negative',
            'negative_unbounded',
        }:
            sm_color = 'magenta'
        elif set(match_statuses) & {'ignore'}:
            sm_color = 'lightsalmon'
    return sm_color


class TemporalSchema(Schema):
    site_preparation: str = None
    active_construction: str = None
    post_construction: str = None


class EvaluationResponseSchema(Schema):
    region_name: str = None
    evaluationId: int = None
    evaluation_run: int = None
    performer: str = None
    evaluation_uuid: str = None
    unionArea: float = None
    statusAnnotated: str = None
    temporalIOU: TemporalSchema = None
    color: str = None


# If the combination of configurationId and regionId has scoring
@router.get('/has_scores')
def has_scores(request: HttpRequest, configuration_id: int, region_id: int):
    # from the hyper parameters we need the evaluation and evaluation_run Ids
    configuration = get_object_or_404(HyperParameters, pk=config_id)
    evaluationId = configuration.evaluation
    performer_name = configuration.performer.slug.lower()
    evaluation_run = configuration.evaluation_run
    region_name = RegionSchema.resolve_name(Region.objects.filter(pk=regionId).first())

    return EvaluationRun.objects.filter(
        evaluation_run_number=evaluation_run,
        evaluation_number=evaluationId,
        region=region_name,
        performer=performer_name,
    ).exists()


# Region scoring Map
@router.get('/region_scoring_colors')
def region_color_map(request: HttpRequest, configuration_id: int, region_id: int):
    # from the hyper parameters we need the evaluation and evaluation_run Ids
    configuration = HyperParameters.objects.filter(pk=configId).first()
    evaluationId = configuration.evaluation
    performer_name = configuration.performer.slug.lower()
    evaluation_run = configuration.evaluation_run
    region_name = RegionSchema.resolve_name(Region.objects.filter(pk=regionId).first())

    evaluation = EvaluationRun.objects.filter(
        evaluation_run_number=evaluation_run,
        evaluation_number=evaluationId,
        region=region_name,
        performer=performer_name,
    ).first()
    if evaluation:
        evaluationUUID = evaluation.uuid
        # Now we can get a list of the  SiteIds information for this evaluationId
        site_list = Site.objects.filter(
            region_id=region_name,
            evaluation_run_uuid=evaluationUUID,
            originator=performer_name,
        )
        colorMappers = {}
        for _i, site in enumerate(site_list):
            site_number = int(
                site.site_id.replace(f'{region_name}_', '').replace(
                    f'_{performer_name}_{site.version}', ''
                )
            )
            colorMappers[
                f'{configId}_{regionId}_{configuration.performer.id}_{site_number}'
            ] = get_site_scoring_color(evaluationUUID, 'overall', site.site_id)

    return colorMappers


# Gets the basic scoring information based on the
# configurationId, regionId SiteNumber and Version
@router.get('/scoring_details', response=EvaluationResponseSchema)
def list_regions(request: HttpRequest, configuration_id: int, region_id: int, siteNumber: int, version: str):
    # from the hyper parameters we need the evaluation and evaluation_run Ids
    configuration = HyperParameters.objects.filter(pk=configId).first()
    evaluationId = configuration.evaluation
    performer_name = configuration.performer.slug.lower()
    evaluation_run = configuration.evaluation_run
    region_name = RegionSchema.resolve_name(Region.objects.filter(pk=regionId).first())

    evaluation = EvaluationRun.objects.filter(
        evaluation_run_number=evaluation_run,
        evaluation_number=evaluationId,
        region=region_name,
        performer=performer_name,
    ).first()
    if evaluation:
        evaluationUUID = evaluation.uuid
        # Now we can get the SiteId information for this evaluationId
        generatedSiteId = (
            f'{region_name}_{siteNumber.zfill(4)}_{performer_name}_{version}'
        )
        logger.warning(generatedSiteId)
        siteObj = Site.objects.filter(
            site_id=generatedSiteId, evaluation_run_uuid=evaluationUUID
        ).first()
        unionArea = siteObj.union_area
        status_annotated = siteObj.status_annotated
        temporalIOU = EvaluationActivityClassificationTemporalIou.objects.filter(
            site_proposal=generatedSiteId,
            evaluation_run_uuid=evaluationUUID,
            activity_type='overall',
        ).first()
        tempDict = {
            'site_preparation': None,
            'active_construction': None,
            'post_construction': None,
        }
        if temporalIOU:
            tempDict = {
                'site_preparation': (temporalIOU.site_preparation),
                'active_construction': (temporalIOU.active_construction),
                'post_construction': (temporalIOU.post_construction),
            }
        # To understand the color associated with it you need
        # to grab the proposals these are the site_truth_matched
        # table from the evaluation_broad_area_search_proposal
        sm_color = get_site_scoring_color(evaluationUUID, 'overall', generatedSiteId)

        return {
            'region_name': region_name,
            'evaluationId': evaluationId,
            'evaluation_run': evaluation_run,
            'performer': performer_name,
            'evaluation_uuid': evaluationUUID,
            'unionArea': unionArea,
            'statusAnnotated': status_annotated,
            'temporalIOU': tempDict,
            'color': sm_color,
        }
    return HttpResponse('Scoring not Found', status=404)
