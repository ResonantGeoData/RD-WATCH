from django.db import models
from django.contrib.auth.models import User

from rdwatch.core.models.annotation_exports import AbstractFileExport


class AnimationSiteExport(AbstractFileExport):
    site_evaluation = models.CharField(max_length=255)

    arguments = models.JSONField(null=True, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class AnimationModelRunExport(AbstractFileExport):
    configuration = models.CharField(max_length=255)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    arguments = models.JSONField(null=True, default=None)
