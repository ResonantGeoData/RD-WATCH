import logging
from celery import shared_task

from django.core.files.uploadedfile import SimpleUploadedFile
import json
from django.core.files import File
from rdwatch.models import SiteObservation
logger = logging.getLogger(__name__)


@shared_task
def generate_video_task(site_observation_id: int) -> None:
    # Sample code for saving a file.
    # TODO: Update this function to actually generate a video

    site_observations = SiteObservation.objects.filter(siteeval=site_observation_id)
    logger.warning(f'Attempting to run generateVideo on site Observation: {site_observation_id}')
    for item in site_observations:
        bbox: tuple[float, float, float, float] = item.geom.extent

        uploaded_file = SimpleUploadedFile(name='foo/bar.txt', content=str(bbox).encode())
        item.video = uploaded_file
        item.save()
