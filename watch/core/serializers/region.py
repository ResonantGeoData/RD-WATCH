import json

import dateutil.parser
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from rest_framework import serializers
from rgd.utility import get_or_create_no_commit
from shapely.geometry import shape
from shapely.wkb import dumps

from watch.core.models import Observation, Region, Site

from .. import models


def populate_geometry(record, feature):
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


class RegionSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        return data

    def to_representation(self, instance: models.Region, include_region: bool = True) -> dict:
        data = {
            'type': 'FeatureCollection',
            'features': [],
        }
        if include_region:
            data['features'].append(
                {
                    'geometry': json.loads(instance.footprint.json),
                    'properties': instance.properties,
                    'type': 'Feature',
                }
            )

        features = models.Site.objects.filter(parent_region=instance).all()
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

        # find index of region
        region_index = None
        for i, feature in enumerate(feature_collection['features']):
            if feature['properties']['type'] == 'region':
                region_index = i
                break
        if region_index is None:
            raise ValueError('No `region` type in FeatureCollection.')
        feature = feature_collection['features'].pop(region_index)

        region, _ = get_or_create_no_commit(
            Region, region_id=feature['properties']['region_id'], properties=feature['properties']
        )
        add_dates(region, feature)
        populate_geometry(region, feature)

        for feature in feature_collection['features']:
            if feature['properties']['type'] == 'region':
                raise ValueError('Multiple `region` types in FeatureCollection.')
            else:
                record, _ = get_or_create_no_commit(
                    Site, site_id=feature['properties']['site_id'], properties=feature['properties']
                )
                record.parent_region = region
            add_dates(record, feature)
            populate_geometry(record, feature)
        return region


class SiteSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        return data

    def to_representation(self, instance: models.Site) -> dict:
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

        features = models.Observation.objects.filter(parent_site=instance).all()
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

        # find index of site
        site_index = None
        for i, feature in enumerate(feature_collection['features']):
            if feature['properties']['type'] == 'site':
                site_index = i
                break
        if site_index is None:
            raise ValueError('No `site` type in FeatureCollection.')
        feature = feature_collection['features'].pop(site_index)

        site, created = get_or_create_no_commit(
            Site,
            site_id=feature['properties']['site_id'],
        )
        if created or not site.properties:
            site.properties = feature['properties']
        if not site.parent_region:
            try:
                site.parent_region = Region.objects.get(
                    region_id=feature['properties']['region_id']
                )
            except Region.DoesNotExist:
                pass
        populate_geometry(site, feature)

        for feature in feature_collection['features']:
            if feature['properties']['type'] == 'site':
                raise ValueError('Multiple `site` types in FeatureCollection.')
            else:
                record, _ = get_or_create_no_commit(
                    Observation, parent_site=site, properties=feature['properties']
                )
                date = feature['properties']['observation_date']
                if date:
                    record.observation_date = dateutil.parser.parse(date)
            populate_geometry(record, feature)
        return site


# 1133 sites, 13 regions
class BasePolygonSerializer(serializers.ModelSerializer):
    outline = serializers.SerializerMethodField()
    footprint = serializers.SerializerMethodField()

    def get_outline(self, obj):
        return json.loads(obj.outline.geojson)

    def get_footprint(self, obj):
        return json.loads(obj.footprint.geojson)


class SiteSerializerBasic(BasePolygonSerializer):
    class Meta:
        model = models.Site
        fields = '__all__'


class RegionSerializerBasic(BasePolygonSerializer):
    class Meta:
        model = models.Region
        fields = '__all__'


class ObservationSerializerBasic(BasePolygonSerializer):
    class Meta:
        model = models.Observation
        fields = '__all__'
