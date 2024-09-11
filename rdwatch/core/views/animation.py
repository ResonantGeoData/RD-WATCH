import logging
from collections.abc import Iterable

from celery.result import AsyncResult
from ninja import Router
from pydantic import UUID4, BaseModel

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rdwatch.core.models import AnimationModelRunExport, AnimationSiteExport
from rdwatch.core.tasks.animation_export import (
    GenerateAnimationSchema,
    create_animation,
    create_modelrun_animation_export,
    create_site_animation_export,
)

logger = logging.getLogger(__name__)

router = Router()


def generate_download_data(
    exports: Iterable[AnimationSiteExport] | Iterable[AnimationModelRunExport],
):
    output = []
    for export in exports:
        if export.export_file:  # File exists it can be downloaded
            output.append(
                {
                    'created': export.created,
                    'completed': True,
                    'arguments': export.arguments,
                    'taskId': export.celery_id,
                }
            )
        else:
            task_id = export.celery_id
            task = AsyncResult(task_id)
            celery_data = {}
            celery_data['state'] = task.state
            celery_data['status'] = task.status
            celery_data['info'] = str(task.info)
            output.append(
                {
                    'created': export.created,
                    'completed': False,
                    'arguments': export.arguments,
                    'taskId': export.celery_id,
                    'state': celery_data,
                }
            )
    return output


@router.post('/site/{id}/')
def generate_site_animation(
    request: HttpRequest,
    id: UUID4,
    params: GenerateAnimationSchema,  # noqa: B008
):
    # Fetch the SiteEvaluation instance
    task_id = create_site_animation_export.delay(
        site_evaluation_id=id, settings=params.dict(), userId=request.user.pk
    )
    return task_id.id


@router.get('/site/{id}/downloads/')
def get_site_downloads(
    request: HttpRequest,
    id: UUID4,
):
    exports = AnimationSiteExport.objects.filter(
        site_evaluation=id, user=request.user
    ).order_by('-created')
    return generate_download_data(exports)


@router.get('/modelrun/{id}/downloads/')
def get_modelrun_downloads(
    request: HttpRequest,
    id: UUID4,
):
    exports = AnimationModelRunExport.objects.filter(
        configuration=id, user=request.user
    ).order_by('-created')
    return generate_download_data(exports)


class DeleteErrorSchema(BaseModel):
    error: str


class DeleteSuccessSchema(BaseModel):
    success: str


@router.delete(
    '/site/{id}/',
    response={
        403: DeleteErrorSchema,
        200: DeleteSuccessSchema,
    },
)
def delete_site_download(
    request: HttpRequest,
    id: UUID4,
):
    # Fetch the export object
    export = get_object_or_404(AnimationSiteExport, celery_id=id, user=request.user)

    # Perform the delete operation
    export.delete()
    return 200, {'success': 'Site Animation Export deleted successfully.'}


@router.delete(
    '/modelrun/{id}/',
    response={
        403: DeleteErrorSchema,
        200: DeleteSuccessSchema,
    },
)
def delete_modelrun_download(
    request: HttpRequest,
    id: UUID4,
):
    # Fetch the export object
    export = get_object_or_404(AnimationModelRunExport, celery_id=id, user=request.user)

    # Perform the delete operation
    export.delete()
    return 200, {'success': 'ModelRun Animation Export deleted successfully.'}


@router.post('/site/{id}/debug/')
def generate_animation_debug(
    request: HttpRequest,
    id: UUID4,
    params: GenerateAnimationSchema,  # noqa: B008
):
    # Fetch the SiteEvaluation instance
    datapath, name = create_animation(
        site_evaluation_id=id,
        settings=params.dict(),
    )
    if datapath:
        with open(datapath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename={name}'
            return response
    return 500, 'Unable to export data'


@router.post('/modelrun/{id}/')
def generate_modelrun_animation(
    request: HttpRequest,
    id: UUID4,
    params: GenerateAnimationSchema,  # noqa: B008
):
    # Fetch the SiteEvaluation instance
    task_id = create_modelrun_animation_export.delay(
        modelrun_id=id, settings=params.dict(), userId=request.user.pk
    )
    return task_id.id


@router.get('/download/site/{task_id}/')
def get_downloaded_site_animation(request: HttpRequest, task_id: UUID4):
    animation_export = get_object_or_404(
        AnimationSiteExport, celery_id=task_id, user=request.user
    )
    name = animation_export.name
    content_type = 'video/mp4'
    if name.endswith('.gif'):
        content_type = 'image/gif'
    response = HttpResponse(
        animation_export.export_file.file, content_type=content_type
    )
    response['Content-Disposition'] = f'attachment; filename="{name}"'
    return response


@router.get('/download/modelrun/{task_id}/')
def get_downloaded_modelrun_animation(request: HttpRequest, task_id: UUID4):
    animation_export = get_object_or_404(
        AnimationModelRunExport, celery_id=task_id, user=request.user
    )
    name = animation_export.configuration.title
    response = HttpResponse(
        animation_export.export_file.file, content_type='application/zip'
    )
    response['Content-Disposition'] = f'attachment; filename="{name}.zip"'
    return response


@router.get('/{task_id}/status/')
def get_animation_status(request: HttpRequest, task_id: UUID4):
    task = AsyncResult(task_id)
    celery_data = {}
    celery_data['state'] = task.state
    celery_data['status'] = task.status
    celery_data['info'] = (
        str(task.info) if isinstance(task.info, RuntimeError) else task.info
    )

    return celery_data
