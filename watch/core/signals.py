import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from rgd.utility import skip_signal

from watch.core import models

logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.Region)
@skip_signal()
def _post_save_region(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))
