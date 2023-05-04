from django.core.files.storage import default_storage
from rest_framework import serializers

from rdwatch.models import SiteImage


class SiteImageSerializer(serializers.Serializer):
    timestamp = serializers.IntegerField()  # type: ignore
    source = serializers.CharField()
    cloudcover = serializers.FloatField()
    image = serializers.SerializerMethodField()
    siteobs_id = serializers.IntegerField()

    class Meta:
        model = SiteImage
        fields = ['timestamp', 'source', 'cloudcover', 'image', 'siteobs_id']

    def get_image(self, obj):
        image = obj.get('image', None)
        if image:
            return default_storage.url(image)
        return None


class SiteImageListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    results = SiteImageSerializer(many=True)
