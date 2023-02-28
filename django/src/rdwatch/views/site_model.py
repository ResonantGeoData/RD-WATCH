from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from rdwatch.models import HyperParameters, SiteEvaluation
from rdwatch.schemas import RegionModel, SiteModel


@api_view(['POST'])
def post_site_model(request: Request, hyper_parameters_id: int):
    try:
        hyper_parameters = HyperParameters.objects.get(pk=hyper_parameters_id)
    except ObjectDoesNotExist:
        raise ValidationError(f"unkown model-run ID: '{hyper_parameters_id}'")

    site_model = SiteModel(**request.data)

    SiteEvaluation.bulk_create_from_site_model(site_model, hyper_parameters)

    return Response(status=201)


@api_view(['POST'])
def post_region_model(request: Request, hyper_parameters_id: int):
    try:
        hyper_parameters = HyperParameters.objects.get(pk=hyper_parameters_id)
    except ObjectDoesNotExist:
        raise ValidationError(f"unknown model-run ID: '{hyper_parameters_id}'")

    region_model = RegionModel(**request.data)

    SiteEvaluation.bulk_create_from_from_region_model(region_model, hyper_parameters)

    return Response(status=201)
