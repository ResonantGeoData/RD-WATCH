from ninja.errors import ValidationError

from django.contrib.gis.db.models import PolygonField
from django.contrib.gis.geos import Polygon
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction

from rdwatch_scoring.models import lookups


class Performer(models.Model):
    id = models.IntegerField(primary_key=True)
    performer_name = models.CharField(max_length=255, null=False)
    performer_code = models.CharField(max_length=255, null=False)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'performer_code_mapping'
