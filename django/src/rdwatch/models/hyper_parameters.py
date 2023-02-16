from django.db import models


class HyperParameters(models.Model):
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

    def __str__(self):
        return self.pk
