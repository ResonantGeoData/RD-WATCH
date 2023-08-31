"""Lookup tables

Lookup tables define the controlled vocabulary of RD-WATCH. They are
small and relatively constant tables.
"""

from django.contrib.postgres.fields import DecimalRangeField
from django.db import models


class Lookup(models.Model):
    id = models.SmallAutoField(primary_key=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self): # This always returns the string
        return self.slug

    class Meta:
        abstract = True


class CommonBand(Lookup):
    spectrum = DecimalRangeField(
        help_text='The spectrum this band captures (μm)',
        db_index=True,
    )


class Constellation(Lookup):
    ...


class ObservationLabel(Lookup):
    ...


class Performer(Lookup):
    ...


class ProcessingLevel(Lookup):
    ...


class RegionClassification(Lookup):
    ...
