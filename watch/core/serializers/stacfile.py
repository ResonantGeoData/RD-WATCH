from rest_framework import serializers
from rgd.models import ChecksumFile
from rgd.serializers import (
    MODIFIABLE_READ_ONLY_FIELDS,
    TASK_EVENT_READ_ONLY_FIELDS,
    ChecksumFileSerializer,
    RelatedField,
)
from rgd_imagery.models import Raster
from rgd_imagery.serializers import RasterSerializer

from .. import models


class STACFileSerializer(serializers.ModelSerializer):
    # TODO: can this writable?
    checksumfile = RelatedField(
        queryset=ChecksumFile.objects.all(), serializer=ChecksumFileSerializer, required=True
    )
    # TODO: make sure this is not a required field
    RelatedField(queryset=Raster.objects.all(), serializer=RasterSerializer, required=False)

    class Meta:
        model = models.STACFile
        fields = '__all__'
        read_only_fields = (
            MODIFIABLE_READ_ONLY_FIELDS
            + TASK_EVENT_READ_ONLY_FIELDS
            + [
                'processed',
                'raster',
            ]
        )
