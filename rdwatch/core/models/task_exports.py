from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver


class AbstractFileExport(models.Model):
    class Meta:
        abstract = True

    export_file = models.FileField(null=True, blank=True, default=None)
    created = models.DateTimeField(
        help_text='The zip file export, deleted 1 hour after creation',
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

    def delete(self, *args, **kwargs):
        if self.export_file:
            self.export_file.delete(save=False)  # Delete the file from storage
        super().delete(*args, **kwargs)  # Call the "real" delete() method of the model


@receiver(models.signals.pre_delete, sender=AbstractFileExport)
def delete_content(sender, instance, **kwargs):
    if instance.export_file:
        instance.export_file.delete(save=False)


class AnnotationExport(AbstractFileExport):
    configuration = models.ForeignKey(
        to='ModelRun',
        on_delete=models.PROTECT,
        help_text='The hyper parameters used for the xport',
        db_index=True,
    )


class AnimationSiteExport(AbstractFileExport):
    site_evaluation = models.ForeignKey(
        to='SiteEvaluation',
        on_delete=models.PROTECT,
        help_text='SiteEvaluation for Animation export',
        db_index=True,
    )
    arguments = models.JSONField(null=True, default=None)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='core_animationsiteexports'
    )


class AnimationModelRunExport(AbstractFileExport):
    configuration = models.ForeignKey(
        to='ModelRun',
        on_delete=models.PROTECT,
        help_text='ModelRun for Animation export',
        db_index=True,
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='core_animationmodelrunexports'
    )
    arguments = models.JSONField(null=True, default=None)
