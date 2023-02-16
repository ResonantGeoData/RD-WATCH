import json
from collections.abc import Iterable
from datetime import datetime
from typing import Literal, TypedDict, cast

import iso3166
from typing_extensions import NotRequired

from django.contrib.gis.geos import GEOSException, GEOSGeometry  # type: ignore
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from rdwatch.models import (
    HyperParameters,
    Region,
    SiteEvaluation,
    SiteObservation,
    lookups,
)


class Polygon(TypedDict):
    type: Literal['Polygon']
    coordinates: list[list[tuple[float, float]]]


class MultiPolygon(TypedDict):
    type: Literal['MultiPolygon']
    coordinates: list[list[list[tuple[float, float]]]]


class SiteFeatureProperties(TypedDict):
    type: Literal['site']
    region_id: str
    site_id: str
    originator: str
    score: NotRequired[float]
    misc_info: NotRequired[dict]


class ObservationFeatureProperties(TypedDict):
    type: Literal['observation']
    observation_date: str | None
    source: str
    sensor_name: str
    current_phase: Literal[
        'No Activity',
        'Site Preparation',
        'Active Construction',
        'Post Construction',
        'Unknown',
    ]
    score: NotRequired[float]


class SiteFeature(TypedDict):
    geometry: Polygon
    properties: SiteFeatureProperties


class ObservationFeature(TypedDict):
    geometry: MultiPolygon
    properties: ObservationFeatureProperties


class SiteFeatureCollection(TypedDict):
    features: list[SiteFeature | ObservationFeature]


class SiteSummaryFeatureProperties(TypedDict):
    type: Literal['site_summary']
    site_id: str
    originator: str
    score: NotRequired[float]
    misc_info: NotRequired[dict]


class RegionFeatureProperties(TypedDict):
    type: Literal['region']
    region_id: str
    originator: str
    score: NotRequired[float]
    misc_info: NotRequired[dict]
    start_date: str
    end_date: str


class SiteSummaryFeature(TypedDict):
    geometry: MultiPolygon
    properties: SiteSummaryFeatureProperties


class RegionFeature(TypedDict):
    geometry: MultiPolygon
    properties: RegionFeatureProperties


class SiteSummaryFeatureCollection(TypedDict):
    features: list[SiteSummaryFeature | RegionFeature]


def get_site_feature(collection: SiteFeatureCollection) -> SiteFeature:
    features: list[SiteFeature] = [
        cast(SiteFeature, feature)
        for feature in collection['features']
        if feature['properties']['type'] == 'site'
    ]
    if len(features) != 1:
        raise ValidationError("must contain exactly one 'Site' feature")
    if features[0].get('geometry', {}).get('type') != 'Polygon':
        raise ValidationError("the 'Site' feature must be a 'Polygon'")
    return features[0]


def get_observation_features(
    collection: SiteFeatureCollection,
) -> list[ObservationFeature]:
    features: list[ObservationFeature] = [
        cast(ObservationFeature, feature)
        for feature in collection['features']
        if feature['properties']['type'] == 'observation'
    ]
    if not features:
        raise ValidationError("must contain one or more 'Observation' features")
    for feature in features:
        if feature.get('geometry', {}).get('type') != 'MultiPolygon':
            raise ValidationError("the 'Observation' feature must be a 'MultiPolygon'")

    return features


def get_region(region_id: str) -> Region:
    countrystr, numstr = region_id.split('_')
    contrynum = iso3166.countries_by_alpha2[countrystr].numeric

    try:
        region_classification = lookups.RegionClassification.objects.get(slug=numstr[0])
    except ObjectDoesNotExist:
        raise ValidationError(f'invalid region classification {numstr[0]}')

    region, _ = Region.objects.get_or_create(
        country=int(contrynum),
        classification=region_classification,
        number=None if numstr[1:] == 'xxx' else int(numstr[1:]),
    )
    return region


def get_site_evaluation(
    feature: SiteFeature,
    region: Region,
    configuration: HyperParameters,
) -> SiteEvaluation:
    site_id = feature['properties']['site_id']
    geojson = json.dumps(feature['geometry'])
    score = feature['properties'].get('score', 1.0)

    try:
        site_number = int(site_id[8:])
    except (IndexError, ValueError):
        raise ValidationError(f"invalid site_id '{site_id}'")

    try:
        geom = GEOSGeometry(geojson)
    except GEOSException:
        raise ValidationError(f"invalid geometry '{geojson}'")

    return SiteEvaluation.objects.create(
        configuration=configuration,
        region=region,
        number=site_number,
        timestamp=datetime.now(),
        geom=geom,
        score=score,
    )


def gen_site_observations(
    features: list[ObservationFeature],
    site_evaluation: SiteEvaluation,
) -> Iterable[SiteObservation]:
    label_set: set[str] = set()
    for feature in features:
        current_phases = feature['properties']['current_phase'].split(', ')
        for current_phase in current_phases:
            label_slug = '_'.join(current_phase.split(' ')).lower()
            label_set.add(label_slug)
    labels_query = lookups.ObservationLabel.objects.filter(slug__in=label_set)
    label_map = {
        ' '.join(label.slug.split('_')).title(): label for label in labels_query
    }

    constellation_set: set[str] = set()
    for feature in features:
        sensor_name = feature['properties']['sensor_name']
        if sensor_name:
            constellation_set.add(sensor_name)
    constellations_query = lookups.Constellation.objects.filter(
        description__in=constellation_set
    )
    constellation_map = {
        constellation.description: constellation
        for constellation in constellations_query
    }

    for feature in features:
        if not feature['properties']['observation_date']:
            continue

        geometries: list[GEOSGeometry] = []
        for polygon_coords in feature['geometry']['coordinates']:
            polygon = {'type': 'MultiPolygon', 'coordinates': [polygon_coords]}
            try:
                geometries.append(GEOSGeometry(json.dumps(polygon)))
            except GEOSException:
                raise ValidationError(f"invalid geometry '{feature['geometry']}'")

        labels: list[lookups.ObservationLabel] = []
        for current_phase in feature['properties']['current_phase'].split(', '):
            if current_phase not in label_map:
                raise ValidationError(f"invalid current_phase '{current_phase}'")
            labels.append(label_map[current_phase])

        if len(labels) > 1 and len(labels) != len(geometries):
            raise ValidationError('inconsistent number of current_phase and geometries')
        elif len(labels) == 1:
            labels *= len(geometries)

        score = feature['properties'].get('score', 1.0)
        observation_date = datetime.strptime(
            feature['properties']['observation_date'],
            '%Y-%m-%d',
        )
        sensor_name = feature['properties']['sensor_name']
        if sensor_name not in constellation_map:
            raise ValidationError(f"invalid sensor_name '{sensor_name}'")
        constellation = constellation_map[sensor_name]

        for geometry, label in zip(geometries, labels):
            yield SiteObservation(
                siteeval=site_evaluation,
                label=label,
                score=score,
                geom=geometry,
                constellation=constellation,
                spectrum=None,
                timestamp=observation_date,
            )


@api_view(['POST'])
@transaction.atomic
def post_site_model(request: Request, hyper_parameters_id: int):
    try:
        hyper_parameters = HyperParameters.objects.get(pk=hyper_parameters_id)
    except ObjectDoesNotExist:
        raise ValidationError(f"unkown model-run ID: '{hyper_parameters_id}'")

    feature_collection = cast(SiteFeatureCollection, request.data)

    try:
        site_feature = get_site_feature(feature_collection)
        region = get_region(site_feature['properties']['region_id'])
        site_evaluation = get_site_evaluation(site_feature, region, hyper_parameters)
        observation_features = get_observation_features(feature_collection)
        SiteObservation.objects.bulk_create(
            gen_site_observations(observation_features, site_evaluation)
        )

    except KeyError as e:
        raise ValidationError(f"malformed site model: no key '{e.args[0]}'")

    return Response(status=201)


def get_site_summary_features(
    collection: SiteSummaryFeatureCollection,
) -> list[SiteSummaryFeature]:
    features: list[SiteSummaryFeature] = [
        cast(SiteSummaryFeature, feature)
        for feature in collection['features']
        if feature['properties']['type'] == 'site_summary'
    ]
    if not len(features):
        raise ValidationError("must contain at least one 'SiteSummary' feature")
    return features


def get_site_summary_region(collection: SiteFeatureCollection) -> Region:
    features: list[RegionFeature] = [
        cast(SiteSummaryFeature, feature)
        for feature in collection['features']
        if feature['properties']['type'] == 'region'
    ]
    if len(features) != 1:
        raise ValidationError("must contain at least one 'RegionSummary' feature")

    region_id = features[0]['properties']['region_id']

    return get_region(region_id)


@api_view(['POST'])
@transaction.atomic
def post_site_summaries(request: Request, hyper_parameters_id: int):
    try:
        hyper_parameters = HyperParameters.objects.get(pk=hyper_parameters_id)
    except ObjectDoesNotExist:
        raise ValidationError(f"unknown model-run ID: '{hyper_parameters_id}'")

    feature_collection = cast(SiteSummaryFeatureCollection, request.data)

    try:
        site_summary_features = get_site_summary_features(feature_collection)

        region_jsons = [
            r['properties']
            for r in feature_collection['features']
            if r['properties']['type'] == 'region'
        ]

        if len(region_jsons) != 1:
            raise ValidationError("must contain exactly one 'region' feature")

        start_date = datetime.strptime(
            region_jsons[0]['start_date'],
            '%Y-%m-%d',
        )
        end_date = datetime.strptime(
            region_jsons[0]['end_date'],
            '%Y-%m-%d',
        )

        # Assign all site-summaries a label of "unknown"
        label = lookups.ObservationLabel.objects.get(slug='unknown')

        region = get_site_summary_region(feature_collection)

        for feature in site_summary_features:
            site_id = feature['properties']['site_id']
            geojson = json.dumps(feature['geometry'])
            score = feature['properties'].get('score', 1.0)

            try:
                site_number = int(site_id[8:])
            except (IndexError, ValueError):
                raise ValidationError(f"invalid site_id '{site_id}'")

            try:
                geom = GEOSGeometry(geojson)
            except GEOSException:
                raise ValidationError(f"invalid geometry '{geojson}'")

            site_evaluation = SiteEvaluation.objects.create(
                configuration=hyper_parameters,
                region=region,
                number=site_number,
                timestamp=datetime.now(),
                geom=geom.convex_hull,
                score=score,
            )

            for timestamp in (start_date, end_date):
                SiteObservation.objects.create(
                    siteeval=site_evaluation,
                    label=label,
                    score=feature['properties']['score'],
                    geom=geom,
                    timestamp=timestamp,
                )

    except KeyError as e:
        raise ValidationError(f"malformed site model: no key '{e.args[0]}'")

    return Response(status=201)
