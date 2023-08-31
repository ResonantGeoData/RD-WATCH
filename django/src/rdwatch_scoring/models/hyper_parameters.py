from django_extensions.db.models import CreationDateTimeField

from django.db import models


class HyperParameters(models.Model):
    uuid = models.CharField(primary_key=True, max_length=1000)
    created = CreationDateTimeField()
    title = models.CharField(max_length=1000)
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

    def __str__(self) -> str:
        return str(self.pk)
