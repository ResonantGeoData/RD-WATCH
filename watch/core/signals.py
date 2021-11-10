from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from rgd.utility import skip_signal

from . import models


@receiver(post_save, sender=models.STACItem)
@skip_signal()
def _post_save_stac_item(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))


@receiver(post_delete, sender=models.STACItem)
@skip_signal()
def _post_delete_stac_item(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_delete(*args, **kwargs))
