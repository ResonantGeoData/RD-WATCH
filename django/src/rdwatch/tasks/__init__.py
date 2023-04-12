from celery import shared_task

from django.core.files.uploadedfile import SimpleUploadedFile

from rdwatch.models import SiteObservation


@shared_task
def generate_video_task(site_observation_id: int) -> None:
    # Sample code for saving a file.
    # TODO: Update this function to actually generate a video

    site_observation = SiteObservation.objects.get(id=site_observation_id)

    bbox: tuple[float, float, float, float] = site_observation.geom.extent

    uploaded_file = SimpleUploadedFile(name='foo/bar.txt', content=str(bbox).encode())

    SiteObservation.objects.filter(id=site_observation_id).update(video=uploaded_file)
