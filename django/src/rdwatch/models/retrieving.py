from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.dispatch import receiver


class Retrieving(models.Model):
    siteeval = models.ForeignKey(
        to='SiteEvaluation',
        on_delete=models.CASCADE,
        db_index=True,
    )
    timestamp = models.DateTimeField(
        help_text="Start time of the task",
    )
    status = models.TextField(blank=True, help_text='Complete, Retrieving, Error')
    error = models.TextField(blank=True, help_text='Error text if an error occurs')

    def __str__(self):
        time = self.timestamp.isoformat()
        return f'{self.siteeval}@{time}'

