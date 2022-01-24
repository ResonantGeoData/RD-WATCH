import json

import dateutil.parser
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from rest_framework import serializers
from shapely.geometry import shape
from shapely.wkb import dumps

from watch.core.models import Feature, Region

from .. import models


class RegionSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        return data

    def to_representation(self, instance: models.Region) -> dict:
        data = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'geometry': json.loads(instance.footprint.json),
                    'properties': instance.properties,
                    'type': 'Feature',
                },
            ],
        }

        features = models.Feature.objects.filter(parent_region=instance).all()
        for feature in features:
            subdata = {
                'geometry': json.loads(feature.footprint.json),
                'properties': feature.properties,
                'type': 'Feature',
            }
            data['features'].append(subdata)
        return data

    @transaction.atomic
    def create(self, data):
        assert data['type'] == 'FeatureCollection'
        feature_collection = data

        def populate(record, feature):
            record.properties = feature['properties']
            geom = shape(feature['geometry'])
            record.footprint = GEOSGeometry(memoryview(dumps(geom)))
            record.outline = GEOSGeometry(memoryview(dumps(geom.envelope)))
            record.save()

        def add_dates(record, feature):
            date = feature['properties']['start_date']
            if date:
                record.start_date = dateutil.parser.parse(date)
            date = feature['properties']['end_date']
            if date:
                record.end_date = dateutil.parser.parse(date)

        # find index of region
        region_index = None
        for i, feature in enumerate(feature_collection['features']):
            if feature['properties']['type'] == 'region':
                region_index = i
                break
        if region_index is None:
            raise ValueError('No `region` type in FeatureCollection.')
        feature = feature_collection['features'].pop(region_index)

        region = Region()
        populate(region, feature)

        for feature in feature_collection['features']:
            if feature['properties']['type'] == 'region':
                raise ValueError('Multiple `region` types in FeatureCollection.')
            else:
                record = Feature()
                record.parent_region = region
                add_dates(record, feature)
            populate(record, feature)
        return region
