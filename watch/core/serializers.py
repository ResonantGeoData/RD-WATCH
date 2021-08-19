from django.contrib.gis.geos import GeometryCollection, GEOSGeometry
from django.db import transaction
from rest_framework import serializers
from shapely.geometry import shape
from shapely.wkb import dumps

from . import models


class RegionSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        return data

    def to_representation(self, instance: models.Region) -> dict:
        data = {
            'type': 'FeatureCollection',
            'features': [],
        }
        features = models.Feature.objects.filter(parent_region=instance).all()
        for feature in features:
            subdata = {
                'geometry': feature.footprint.json,
                'properties': feature.properties,
                'type': 'Feature',
            }
            data['features'].append(subdata)
        return data

    @transaction.atomic
    def create(self, data):
        assert data['type'] == 'FeatureCollection'
        geometries = []
        for json_feature in data.get('features', []):
            geometries.append(GEOSGeometry(memoryview(dumps(shape(json_feature['geometry'])))))
        instance = models.Region()
        instance.footprint = GeometryCollection(*geometries)
        instance.outline = instance.footprint.convex_hull
        instance.skip_signal = True
        instance.save()
        for i, json_feature in enumerate(data.get('features', [])):
            properties = json_feature['properties']
            feature = models.Feature()
            feature.parent_region = instance
            feature.properties = properties
            feature.footprint = geometries[i]
            feature.outline = feature.footprint.convex_hull
            feature.start_date = properties['start_date']
            feature.end_date = properties['end_date']
            feature.save()
        return instance
