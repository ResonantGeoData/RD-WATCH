from uuid import uuid4

from s3_file_field import S3FileField

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class ModelRunUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    title = models.CharField(max_length=1000)
    private = models.BooleanField(
        default=False, help_text='Whether this model run should be private'
    )
    region = models.CharField(
        max_length=1000,
        blank=True,
        help_text='Override for the region this model run belongs to',
    )
    performer = models.CharField(
        max_length=1000,
        blank=True,
        help_text='Shortcode override for the team that produced this evaluation',
    )
    zipfile = S3FileField()

    task_id = models.CharField(max_length=256, help_text='Celery task ID')

    def __str__(self) -> str:
        return f'<ModelRunUpload {self.id}>'


@receiver(pre_delete, sender=ModelRunUpload)
def delete_zipfile(sender, instance, **kwargs):
    if instance.zipfile:
        instance.zipfile.delete(save=False)
