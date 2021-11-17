from rest_framework import serializers
from rgd.serializers import MODIFIABLE_READ_ONLY_FIELDS, TASK_EVENT_READ_ONLY_FIELDS

from .. import models


class GoogleCloudRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoogleCloudRecord
        fields = '__all__'
        read_only_fields = MODIFIABLE_READ_ONLY_FIELDS + TASK_EVENT_READ_ONLY_FIELDS
