from ninja import Router
from ninja.pagination import PageNumberPagination, paginate
from ninja.responses import Response

from django.http import HttpRequest

from rdwatch.core.models import Region
from rdwatch.core.schemas import RegionModel

router = Router()


@router.get('/', response=list[str])
@paginate(PageNumberPagination, page_size=1000)
def list_regions(request: HttpRequest):
    return Region.objects.values_list('name', flat=True)


@router.get('/details', response=list[dict])
@paginate(PageNumberPagination, page_size=1000)
def list_region_details(request: HttpRequest):
    regions = Region.objects.values_list('name', 'owner__username', 'public')
    return [
        {
            'name': region[0],
            'owner': region[1] if region[1] is not None else 'None',
            'public': region[2],
        }
        for region in regions
    ]


@router.post('/')
def post_region_model_editor(
    request: HttpRequest,
    region_model: RegionModel,
):
    owner = request.user
    # Extract the owner from the request user
    region, created = Region.create_region_model_from_geoJSON(region_model, True, owner)

    return Response(
        {'detail': 'Region model created successfully', 'region_id': str(region.name)},
        status=201,
    )
