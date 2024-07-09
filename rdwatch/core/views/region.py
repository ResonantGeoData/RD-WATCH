import json
import tempfile

from ninja import Router
from ninja.pagination import PageNumberPagination, paginate
from ninja.responses import Response

from django.db import connection
from django.db.models import BooleanField, F, Field, Func, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from rdwatch.core.models import ModelRun, Region
from rdwatch.core.schemas import RegionModel

router = Router()


# indicates why a region can't be deleted by the current User
def get_delete_block(region_id, user):
    region = Region.objects.get(pk=region_id)
    if region.owner is None and region.public:
        return 'Region is a System Region that is Public'
    if region.owner != user:
        return 'You do not have permission to delete this region.'
    if ModelRun.objects.filter(region=region_id).exists():
        return (
            'This region is currently being used in model runs and cannot be deleted.'
        )
    return False


@router.get('/', response=list[str])
@paginate(PageNumberPagination, page_size=1000)
def list_regions(request: HttpRequest):
    return Region.objects.values_list('name', flat=True)


@router.get('/details/', response=list[dict])
@paginate(PageNumberPagination, page_size=1000)
def list_region_details(request: HttpRequest):
    regions = Region.objects.values_list(
        'name', 'owner__username', 'public', 'pk', 'geom'
    )
    return [
        {
            'name': region[0],
            'owner': region[1] if region[1] is not None else 'None',
            'value': region[0] if region[1] is None else f'{region[0]}_{region[1]}',
            'public': region[2],
            'id': region[3],
            'deleteBlock': get_delete_block(region[3], request.user),
            'hasGeom': True if region[4] else False,
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
    region, _created = Region.create_region_model_from_geoJSON(
        region_model, True, owner
    )

    return Response(
        {'detail': 'Region model created successfully', 'region_id': region.name},
        status=201,
    )


@router.delete('/{region_id}/')
def delete_region(request: HttpRequest, region_id: int):
    owner = request.user
    selected_region = get_object_or_404(Region, pk=region_id)
    if selected_region.owner != owner:  # 403 response, only owner can delete a region
        return JsonResponse(
            {'error': 'You do not have permission to delete this region.'}, status=403
        )

    # check and see if any model runs utilize this region
    region_model_runs = ModelRun.objects.filter(region=region_id).count()
    if region_model_runs > 0:  # we seend back an error that the model run is invalid
        return JsonResponse(
            {
                'error': 'This region is currently being\
                used in model runs and cannot be deleted.'
            },
            status=400,
        )
    # return a successful response for deletion of the region
    selected_region.delete()
    return JsonResponse({'success': 'Region deleted successfully.'}, status=200)


@router.get('/{region_id}/vector-tile/{z}/{x}/{y}.pbf/')
def vector_tile(request: HttpRequest, region_id: int, z: int, x: int, y: int):
    envelope = Func(z, x, y, function='ST_TileEnvelope')
    intersects = Q(
        Func(
            'geom',
            envelope,
            function='ST_Intersects',
            output_field=BooleanField(),
        )
    )
    mvtgeom = Func(
        'geom',
        envelope,
        function='ST_AsMVTGeom',
        output_field=Field(),
    )

    regions_queryset = (
        Region.objects.filter(pk=region_id)
        .filter(intersects)
        .values()
        .annotate(
            name=F('name'),
            mvtgeom=mvtgeom,
        )
    )
    (
        regions_sql,
        regions_params,
    ) = regions_queryset.query.sql_with_params()

    sql = f"""
        WITH
            regions AS ({regions_sql})
        SELECT (
            (
                SELECT ST_AsMVT(regions.*, %s, 4096, 'mvtgeom')
                FROM regions
            )
        )
    """  # noqa: E501
    params = regions_params + (f'regions-{region_id}',)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    tile = row[0]

    return HttpResponse(
        tile,
        content_type='application/octet-stream',
        status=200 if tile else 204,
    )


@router.get('/{id}/download/')
def download_annotations(request: HttpRequest, id: int):
    region = Region.objects.get(pk=id)
    output = region.to_feature_collection()
    if output is not None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            json_data = json.dumps(output).encode('utf-8')
            temp_file.write(json_data)

        # Return the temporary file for download
        with open(temp_file.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response[
                'Content-Disposition'
            ] = f'attachment; filename={region.value}.geojson'

            return response
    # TODO: Some Better Error response
    return 500, 'Unable to export data'
