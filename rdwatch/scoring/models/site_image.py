from django.contrib.postgres.indexes import GistIndex
from django.db import models

from rdwatch.core.models.site_image import BaseSiteImage


class SiteImage(BaseSiteImage):
    site = models.CharField(max_length=255)
    observation = models.CharField(max_length=255)

    class Meta:
        indexes = [GistIndex(fields=['timestamp'])]
