import logging
import math

from ninja import Schema
from ninja.pagination import RouterPaginated

# Create your views here.
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models import ModelRun

from ..models import(
    EvaluationActivityClassificationTemporalIou,
    EvaluationBroadAreaSearchDetection,
    EvaluationRun,
    Site
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
    site_preparation: str | None = None
    active_construction: str | None = None
    post_construction: str | None = None


class EvaluationResponseSchema(Schema):
    region_name: str
    evaluationId: int
    evaluation_run: int
    performer: str
    evaluation_uuid: str
    unionArea: float | None = None
    statusAnnotated: str | None = None
    temporalIOU: TemporalSchema | None = None
    color: str


# If the combination of configurationId and regionId has scoring
@router.get('/has-scores')
def has_scores(request: HttpRequest, configurationId: int, region: str):
    # from the hyper parameters we need the evaluation and evaluation_run Ids
    configuration = get_object_or_404(
        ModelRun.objects.select_related('performer'), pk=configurationId
    )
    evaluationId = configuration.evaluation
    performer_name = configuration.performer.slug.lower()
    evaluation_run = configuration.evaluation_run

    if evaluation_run is None or evaluationId is None:
        return False

    return EvaluationRun.objects.filter(
        evaluation_run_number=evaluation_run,
        evaluation_number=evaluationId,
        region=region,
        performer=performer_name,
    ).exists()


# Region scoring Map
@router.get('/region-colors')
def region_color_map(request: HttpRequest, configurationId: int, region: str):
    # from the hyper parameters we need the evaluation and evaluation_run Ids
    configuration = ModelRun.objects.filter(pk=configurationId).first()
    evaluationId = configuration.evaluation
    performer_name = configuration.performer.slug.lower()
    evaluation_run = configuration.evaluation_run

    evaluation = EvaluationRun.objects.filter(
        evaluation_run_number=evaluation_run,
        evaluation_number=evaluationId,
        region=region,
        performer=performer_name,
    ).first()
    if evaluation:
        evaluationUUID = evaluation.uuid
        # Now we can get a list of the  SiteIds information for this evaluationId
        site_list = Site.objects.filter(
            region_id=region,
            evaluation_run_uuid=evaluationUUID,
            originator=performer_name,
        )
        colorMappers = {}
        for site in site_list:
            site_number = int(
                site.site_id.replace(f'{region}_', '').replace(
                    f'_{performer_name}_{site.version}', ''
                )
            )
            colorMappers[
                f'{configurationId}_{region}_{configuration.performer.id}_{site_number}'  # noqa: E501
            ] = get_site_scoring_color(evaluationUUID, 'overall', site.site_id)

    return colorMappers


# Gets the basic scoring information based on the
# configurationId, regionId SiteNumber and Version
@router.get('/details')
def list_regions(
    request: HttpRequest,
    configurationId: int,
    region: str,
    siteNumber: int,
    version: str,
):
    # from the hyper parameters we need the evaluation and evaluation_run Ids
    configuration = ModelRun.objects.filter(pk=configurationId).first()
    evaluationId = configuration.evaluation
    performer_name = configuration.performer.slug.lower()
    evaluation_run = configuration.evaluation_run

    evaluation = get_object_or_404(
        EvaluationRun,
        evaluation_run_number=evaluation_run,
        evaluation_number=evaluationId,
        region=region,
        performer=performer_name,
    )
    evaluationUUID = evaluation.uuid
    # Now we can get the SiteId information for this evaluationId
    generatedSiteId = f'{region}_{str(siteNumber).zfill(4)}_{performer_name}_{version}'
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
        site_preparation = (
            temporalIOU.site_preparation
            if not math.isnan(temporalIOU.site_preparation)
            else 0
        )
        active_construction = (
            temporalIOU.active_construction
            if not math.isnan(temporalIOU.active_construction)
            else 0
        )
        post_construction = (
            temporalIOU.post_construction
            if not math.isnan(temporalIOU.post_construction)
            else 0
        )
        tempDict = {
            'site_preparation': (site_preparation),
            'active_construction': (active_construction),
            'post_construction': (post_construction),
        }
    # To understand the color associated with it you need
    # to grab the proposals these are the site_truth_matched
    # table from the evaluation_broad_area_search_proposal
    sm_color = get_site_scoring_color(evaluationUUID, 'overall', generatedSiteId)

    return {
        'region_name': region,
        'evaluationId': evaluationId,
        'evaluation_run': evaluation_run,
        'performer': performer_name,
        'evaluation_uuid': evaluationUUID,
        'unionArea': unionArea,
        'statusAnnotated': status_annotated,
        'temporalIOU': tempDict,
        'color': sm_color,
    }
