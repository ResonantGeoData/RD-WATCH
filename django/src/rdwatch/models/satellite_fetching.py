from django.db import models


class SatelliteFetching(models.Model):
    class Status(models.TextChoices):
        COMPLETE = 'Complete'
        RUNNING = 'Running'
        ERROR = 'Error'

    siteeval = models.OneToOneField(
        to='SiteEvaluation',
        on_delete=models.CASCADE,
        db_index=True,
        related_name='satellite_fetching',
    )
    configuration = models.ForeignKey(
        to='HyperParameters',
        on_delete=models.PROTECT,
        help_text='The hyper parameters used this site evaluation.',
        blank=True,
        null=True,
    )
    timestamp = models.DateTimeField(
        help_text='Start time of the task',
    )
    status = models.CharField(
        max_length=255,  # If we need future states
        blank=True,
        help_text='Fetching Status',
        choices=Status.choices,
    )
    celery_id = models.CharField(
        max_length=255,  # If we need future states
        blank=True,
        help_text='Celery Task Id',
    )

    error = models.TextField(blank=True, help_text='Error text if an error occurs')

    def __str__(self):
        time = self.timestamp.isoformat()
        return f'{self.siteeval}@{time}'
