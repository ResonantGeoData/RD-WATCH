from django.contrib.postgres.indexes import GistIndex
from django.db import models


class SatelliteFetching(models.Model):
    class Status(models.TextChoices):
        COMPLETE = "Complete"
        RUNNING = "Running"
        ERROR = "Error"
    siteeval = models.ForeignKey(
        to='SiteEvaluation',
        on_delete=models.CASCADE,
        db_index=True,
    )
    timestamp = models.DateTimeField(
        help_text="Start time of the task",
    )
    status = models.CharField(
        max_length=255,  # If we need future states
        blank=True,
        help_text='Fetching Status',
        choices=Status.choices)
    error = models.TextField(blank=True, help_text='Error text if an error occurs')

    def __str__(self):
        time = self.timestamp.isoformat()
        return f'{self.siteeval}@{time}'

