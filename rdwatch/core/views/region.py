import json
import tempfile

from ninja import Router, Schema
from ninja.pagination import PageNumberPagination, paginate

from django.db import connection
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Exists,
    F,
    Field,
    Func,
    OuterRef,
    Q,
    Value,
    When,
)
from django.db.models.functions import Concat
from django.http import HttpRequest, HttpResponse
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


class RegionDetailSchema(Schema):
    name: str
    ownerUsername: str
    value: str
    public: bool
    id: int
    deleteBlock: str  # empty when a region can be deleted
    hasGeom: bool


@router.get('/details/', response=list[RegionDetailSchema])
@paginate(PageNumberPagination, page_size=1000)
def list_region_details(request: HttpRequest):
    user = request.user
    model_run_exists = ModelRun.objects.filter(region=OuterRef('pk')).values('pk')
    regions = Region.objects.annotate(
        ownerUsername=Case(
            When(Q(owner__isnull=False), then=F('owner__username')),
            When(Q(owner__isnull=True), then=Value('None')),
            default=Value('None'),
            output_field=CharField(),
        ),
        value=Case(
            When(owner__username__isnull=True, then=F('name')),
            default=Concat(F('name'), Value('_'), F('owner__username')),
            output_field=CharField(),
        ),
        hasGeom=Case(
            When(geom__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        deleteBlock=Case(
            When(
                Q(owner__isnull=True) & Q(public=True),
                then=Value('Region is a System Region that is Public'),
            ),
            When(
                Q(owner__isnull=False) & ~Q(owner=user),
                then=Value('You do not have permission to delete this region.'),
            ),
            When(
                Exists(model_run_exists),
                then=Value(
                    'This region is currently being used in model\
                    runs and cannot be deleted.'
                ),
            ),
            default=Value(''),
            output_field=CharField(),
        ),
    ).values('name', 'ownerUsername', 'value', 'public', 'id', 'hasGeom', 'deleteBlock')
    return regions


class RegionPostSchema(Schema):
    detail: str
    region_id: str


@router.post('/', response={201: RegionPostSchema})
def post_region_model_editor(
    request: HttpRequest,
    region_model: RegionModel,
):
    owner = request.user
    # Extract the owner from the request user
    region, _created = Region.create_region_model_from_geoJSON(
        region_model, True, owner
    )

    return 201, {
        'detail': 'Region model created successfully',
        'region_id': region.value,
    }


class RegionDeleteErrorSchema(Schema):
    error: str


class RegionDeleteSuccessSchema(Schema):
    success: str


@router.delete(
    '/{region_id}/',
    response={
        403: RegionDeleteErrorSchema,
        400: RegionDeleteErrorSchema,
        200: RegionDeleteSuccessSchema,
    },
)
def delete_region(request: HttpRequest, region_id: int):
    owner = request.user
    selected_region = get_object_or_404(Region, pk=region_id)
    if selected_region.owner != owner:  # 403 response, only owner can delete a region
        return 403, {'error': 'You do not have permission to delete this region.'}

    # check and see if any model runs utilize this region
    region_model_runs = ModelRun.objects.filter(region=region_id).count()
    if region_model_runs > 0:  # we seend back an error that the model run is invalid
        return 400, {
            'error': 'This region is currently being\
                used in model runs and cannot be deleted.'
        }
    # return a successful response for deletion of the region
    selected_region.delete()
    return 200, {'success': 'Region deleted successfully.'}


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
