from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_load_google_cloud_record(record_pk):
    from watch.core.models import GoogleCloudRecord
    from watch.core.tasks.ingest import load_google_cloud_record

    record = GoogleCloudRecord.objects.get(pk=record_pk)
    helpers._run_with_failure_reason(record, load_google_cloud_record, record_pk)
