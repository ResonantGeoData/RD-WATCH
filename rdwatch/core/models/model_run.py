from uuid import uuid4

from django_extensions.db.models import CreationDateTimeField

from django.contrib.auth.models import User
from django.db import models


class ModelRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

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
    evaluation = models.IntegerField(blank=True, null=True)
    evaluation_run = models.IntegerField(blank=True, null=True)
    expiration_time = models.DurationField(
        null=True,
        blank=True,
        help_text='Time relative to creation that this model run should be deleted.',
    )

    region = models.ForeignKey(
        to='Region',
        on_delete=models.PROTECT,
        help_text='The region this model run belongs to',
        db_index=True,
        related_name='model_runs',
    )

    class ProposalStatus(models.TextChoices):
        PROPOSAL = (
            'PROPOSAL'  # proposal is a proposal awaiting Adjudication/Confirmation
        )
        APPROVED = 'APPROVED'  # proposal is approved and merged into ground truth

    proposal = models.CharField(
        max_length=255,  # If we need future states
        blank=True,
        null=True,
        help_text='Fetching Status',
        choices=ProposalStatus.choices,
    )
    ground_truth = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    public = models.BooleanField(default=True)

    def __str__(self) -> str:
        return str(self.pk)
