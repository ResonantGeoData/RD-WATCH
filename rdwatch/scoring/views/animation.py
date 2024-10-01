import logging
from collections.abc import Iterable

from celery.result import AsyncResult
from ninja import Router
from pydantic import UUID4

from django.core.files.storage import default_storage
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.core.views.animation import DeleteErrorSchema, DeleteSuccessSchema
from rdwatch.scoring.models import (
    AnimationModelRunExport,
    AnimationSiteExport,
    EvaluationRun,
)
from rdwatch.scoring.tasks.animation_export import (
    GenerateAnimationSchema,
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
            celery_data['info'] = (
                str(task.info) if isinstance(task.info, Exception) else task.info
            )
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
    logger.warning(f'Found: {exports.exists()} with id: {id}')
    return generate_download_data(exports)


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
    presigned_url = default_storage.url(animation_export.export_file.name)
    return {'url': presigned_url, 'filename': name}


@router.get('/download/modelrun/{task_id}/')
def get_downloaded_modelrun_animation(request: HttpRequest, task_id: UUID4):
    animation_export = get_object_or_404(
        AnimationModelRunExport, celery_id=task_id, user=request.user
    )
    model_run = EvaluationRun.objects.get(pk=animation_export.configuration)
    title = f'Eval_{model_run.evaluation_number}_{model_run.evaluation_run_number}_{model_run.performer}'  # noqa: E501
    name = f'{title}.zip'
    presigned_url = default_storage.url(animation_export.export_file.name)
    return {'url': presigned_url, 'filename': name}


@router.get('/{task_id}/status/')
def get_animation_status(request: HttpRequest, task_id: UUID4):
    task = AsyncResult(task_id)
    celery_data = {}
    celery_data['state'] = task.state
    celery_data['status'] = task.status
    if isinstance(task.info, Exception):
        celery_data['error'] = str(task.info)
    else:
        celery_data['info'] = task.info
    return celery_data


@router.post('/{task_id}/cancel/')
def cancel_animation_status(request: HttpRequest, task_id: UUID4):
    try:
        export_record = AnimationSiteExport.objects.get(celery_id=task_id)
    except AnimationSiteExport.DoesNotExist:
        export_record = AnimationModelRunExport.objects.get(celery_id=task_id)
    if export_record:
        with transaction.atomic():
            # Use select_for_update here to lock the AnimationExport row
            # for the duration of this transaction in order to ensure its
            # status doesn't change out from under us
            export_record.delete()
            task = AsyncResult(task_id)
            if task:
                task.revoke(terminate=True)
            return 202
    return 404
