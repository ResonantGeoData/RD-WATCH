from django_extensions.db.models import CreationDateTimeField

from django.db import models


class HyperParameters(models.Model):
    created = CreationDateTimeField()
    title = models.CharField(max_length=1000)
    performer = models.ForeignKey(
        to='Performer',
        on_delete=models.PROTECT,
        help_text='The team that produced this evaluation',
        db_index=True,
    )
    parameters = models.JSONField(
        help_text='The hyper parameters for an ML task',
        db_index=True,
    )
    expiration_time = models.DurationField(
        null=True,
        blank=True,
        help_text='Time relative to creation that this model run should be deleted.',
    )

    def __str__(self):
        return self.pk
