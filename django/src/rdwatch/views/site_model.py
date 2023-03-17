from ninja import Router

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models import HyperParameters, SiteEvaluation
from rdwatch.schemas import RegionModel, SiteModel

router = Router()


@router.post('/{hyper_parameters_id}/site-model')
def post_site_model(
    request: HttpRequest,
    hyper_parameters_id: int,
    site_model: SiteModel,
):
    hyper_parameters = get_object_or_404(HyperParameters, pk=hyper_parameters_id)
    SiteEvaluation.bulk_create_from_site_model(site_model, hyper_parameters)
    return 201


@router.post('/{hyper_parameters_id}/region-model')
def post_region_model(
    request: HttpRequest,
    hyper_parameters_id: int,
    region_model: RegionModel,
):
    hyper_parameters = get_object_or_404(HyperParameters, pk=hyper_parameters_id)
    SiteEvaluation.bulk_create_from_from_region_model(region_model, hyper_parameters)
    return 201
