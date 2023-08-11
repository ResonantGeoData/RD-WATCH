from django.db import models
from django.dispatch import receiver


class AnnotationExport(models.Model):
    configuration = models.ForeignKey(
        to='HyperParameters',
        on_delete=models.PROTECT,
        help_text='The hyper parameters used for the xport',
        db_index=True,
    )
    export_file = models.FileField(null=True, blank=True)
    created = models.DateTimeField(
        help_text='The annotation file export, will be deleted 1 hour after creation',
    )
    name = models.CharField(
        max_length=1024,
        blank=True,
        help_text='Name of the model run for download',
    )
    celery_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Celery Task Id',
    )


@receiver(models.signals.pre_delete, sender=AnnotationExport)
def delete_content(sender, instance, **kwargs):
    if instance.export_file:
        instance.export_file.delete(save=False)
