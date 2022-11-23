import json
from datetime import datetime
from typing import Iterable, Literal, TypedDict, cast

import iso3166
from typing_extensions import NotRequired

from django.contrib.gis.geos import GEOSException, GEOSGeometry
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


class MultiPolygon(TypedDict):
    type: Literal["MultiPolygon"]
    coordinates: list[list[list[tuple[float, float]]]]


class SiteFeatureProperties(TypedDict):
    type: Literal["site"]
    region_id: str
    site_id: str
    originator: str
    score: NotRequired[float]
    misc_info: NotRequired[dict]


class ObservationFeatureProperties(TypedDict):
    type: Literal["observation"]
    observation_date: str | None
    source: str
    sensor_name: str
    current_phase: Literal[
        "No Activity",
        "Site Preparation",
        "Active Construction",
        "Post Construction",
        "Unknown",
    ]
    score: NotRequired[float]


class SiteFeature(TypedDict):
    geometry: dict
    properties: SiteFeatureProperties


class ObservationFeature(TypedDict):
    geometry: MultiPolygon
    properties: ObservationFeatureProperties


class FeatureCollection(TypedDict):
    features: list[SiteFeature | ObservationFeature]


def get_site_feature(collection: FeatureCollection) -> SiteFeature:
    features: list[SiteFeature] = [
        cast(SiteFeature, feature)
        for feature in collection["features"]
        if feature["properties"]["type"] == "site"
    ]
    if len(features) != 1:
        raise ValidationError("must contain exactly one 'Site' feature")
    return features[0]


def get_observation_features(collection: FeatureCollection) -> list[ObservationFeature]:
    features: list[ObservationFeature] = [
        cast(ObservationFeature, feature)
        for feature in collection["features"]
        if feature["properties"]["type"] == "observation"
    ]
    if not features:
        raise ValidationError("must contain one or more 'Observation' features")
    return features


def get_region(region_id: str) -> Region | None:
    countrystr, numstr = region_id.split("_")
    contrynum = iso3166.countries_by_alpha2[countrystr].numeric

    try:
        region_classification = lookups.RegionClassification.objects.get(slug=numstr[0])
    except ObjectDoesNotExist:
        raise ValidationError(f"invalid region classification {numstr[0]}")

    region, _ = Region.objects.get_or_create(
        country=int(contrynum),
        classification=region_classification,
        number=None if numstr[1:] == "xxx" else int(numstr[1:]),
    )
    return region


def get_hyper_parameters(feature: SiteFeature) -> HyperParameters:
    originator = feature["properties"]["originator"]
    misc_info = feature["properties"].get("misc_info", dict())

    try:
        performer = lookups.Performer.objects.get(slug=originator.upper())
    except ObjectDoesNotExist:
        raise ValidationError(f"unkown originator '{originator}'")

    return HyperParameters.objects.create(performer=performer, parameters=misc_info)


def get_site_evaluation(
    feature: SiteFeature,
    region: Region,
    configuration: HyperParameters,
) -> SiteEvaluation:
    site_id = feature["properties"]["site_id"]
    geojson = json.dumps(feature["geometry"])
    score = feature["properties"].get("score", 1.0)

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
        current_phases = feature["properties"]["current_phase"].split(", ")
        for current_phase in current_phases:
            label_slug = "_".join(current_phase.split(" ")).lower()
            label_set.add(label_slug)
    labels_query = lookups.ObservationLabel.objects.filter(slug__in=label_set)
    label_map = {
        " ".join(label.slug.split("_")).title(): label for label in labels_query
    }

    constellation_set: set[str] = set()
    for feature in features:
        sensor_name = feature["properties"]["sensor_name"]
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
        if not feature["properties"]["observation_date"]:
            continue

        geometries: list[GEOSGeometry] = []
        for polygon_coords in feature["geometry"]["coordinates"]:
            polygon = {"type": "MultiPolygon", "coordinates": [polygon_coords]}
            try:
                geometries.append(GEOSGeometry(json.dumps(polygon)))
            except GEOSException:
                raise ValidationError(f"invalid geometry '{feature['geometry']}'")

        labels: list[lookups.ObservationLabel] = []
        for current_phase in feature["properties"]["current_phase"].split(", "):
            if current_phase not in label_map:
                raise ValidationError(f"invalid current_phase '{current_phase}'")
            labels.append(label_map[current_phase])

        if len(labels) > 1 and len(labels) != len(geometries):
            raise ValidationError("inconsistent number of current_phase and geometries")
        elif len(labels) == 1:
            labels *= len(geometries)

        score = feature["properties"].get("score", 1.0)
        observation_date = datetime.strptime(
            feature["properties"]["observation_date"],
            "%Y-%m-%d",
        )
        sensor_name = feature["properties"]["sensor_name"]
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


@api_view(["POST"])
@transaction.atomic
def post_site_model(request: Request):
    feature_collection = cast(FeatureCollection, request.data)

    try:
        site_feature = get_site_feature(feature_collection)
        region = get_region(site_feature["properties"]["region_id"])
        hyper_parameters = get_hyper_parameters(site_feature)
        site_evaluation = get_site_evaluation(site_feature, region, hyper_parameters)
        observation_features = get_observation_features(feature_collection)
        SiteObservation.objects.bulk_create(
            gen_site_observations(observation_features, site_evaluation)
        )

    except KeyError as e:
        raise ValidationError(f"malformed site model: no key '{e.args[0]}'")

    return Response()
