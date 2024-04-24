from abc import abstractmethod

from django.db import models


class BaseSatelliteFetching(models.Model):
    class Meta:
        abstract = True

    class Status(models.TextChoices):
        COMPLETE = 'Complete'
        RUNNING = 'Running'
        ERROR = 'Error'

    @property
    @abstractmethod
    def site(self):
        raise NotImplementedError()

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

    def __str__(self) -> str:
        time = self.timestamp.isoformat()
        return f'{self.site}@{time}'


class SatelliteFetching(BaseSatelliteFetching):
    site = models.OneToOneField(
        to='SiteEvaluation',
        on_delete=models.CASCADE,
        db_index=True,
        related_name='satellite_fetching',
    )

    class Meta:
        indexes = [
            models.Index(fields=['status']),
        ]
