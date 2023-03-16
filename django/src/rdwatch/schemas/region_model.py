# flake8: noqa: F722
import json
from datetime import datetime
from typing import Any, Literal

from ninja import Schema
from pydantic import constr, validator

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon


class RegionFeature(Schema):
    type: Literal['region']
    region_id: constr(regex=r'^[A-Z]{2}_[RCST]\d{3}$')
    version: str | None
    mgrs: str
    model_content: Literal['empty', 'annotation', 'proposed'] | None
    start_date: datetime | None
    end_date: datetime | None
    originator: Literal[
        'te',
        'pmo',
        'acc',
        'ara',
        'ast',
        'bla',
        'iai',
        'kit',
        'str',
        'iMERIT',
        'imerit',
    ]

    # Optional fields
    comments: str | None
    performer_cache: dict[Any, Any] | None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')


class SiteSummaryFeature(Schema):
    type: Literal['site_summary']
    site_id: constr(regex=r'^[A-Z]{2}_[RCST]\d{3}_\d{4}$')
    version: str | None
    mgrs: str
    status: Literal[
        'positive_annotated',
        'positive_partial',
        'positive_annotated_static',
        'positive_partial_static',
        'positive_pending',
        'positive_excluded',
        'negative',
        'ignore',
        'transient_positive',
        'transient_negative',
        'system_proposed',
        'system_confirmed',
        'system_rejected',
    ]
    start_date: datetime | None
    end_date: datetime | None
    model_content: Literal['annotation', 'proposed'] | None
    originator: Literal[
        'te',
        'pmo',
        'acc',
        'ara',
        'ast',
        'bla',
        'iai',
        'kit',
        'str',
        'iMERIT',
        'imerit',
    ]

    # Optional fields
    comments: str | None
    score: float | None
    validated: Literal['True', 'False'] | None
    annotation_cache: dict[Any, Any] | None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')

    @property
    def site_number(self) -> int:
        return int(self.site_id[8:])


class Feature(Schema):
    class Config:
        arbitrary_types_allowed = True

    type: Literal['Feature']
    properties: RegionFeature | SiteSummaryFeature
    geometry: MultiPolygon

    @validator('geometry', pre=True)
    def parse_geometry(cls, v: dict[str, Any]):
        geom = GEOSGeometry(json.dumps(v))
        if isinstance(geom, Polygon):
            geom = MultiPolygon(geom)
        return geom


class RegionModel(Schema):
    type: Literal['FeatureCollection']
    features: list[Feature]

    @validator('features', pre=True)
    def preprocess_features(cls, v: list):
        return _preprocess_features(v)

    @validator('features')
    def ensure_one_region_feature(cls, v: list[Feature]):
        region_features = [
            feature for feature in v if isinstance(feature.properties, RegionFeature)
        ]
        if len(region_features) != 1:
            raise ValueError('More than one "region" feature was detected.')
        return v

    @property
    def region_feature(self) -> Feature:
        return [
            feature
            for feature in self.features
            if isinstance(feature.properties, RegionFeature)
        ][0]

    @property
    def site_summary_features(self) -> list[Feature]:
        return [
            feature
            for feature in self.features
            if isinstance(feature.properties, SiteSummaryFeature)
        ]


def _preprocess_features(features: list) -> list:
    for feature in features:
        if (
            feature['properties']['type'] == 'site_summary'
            and 'region_id' in feature['properties']
        ):
            del feature['properties']['region_id']

        for key, value in feature['properties'].items():
            if isinstance(value, str):
                feature['properties'][key] = value.strip()

        if 'model_cont' in feature['properties']:
            feature['properties']['model_content'] = feature['properties']['model_cont']
            del feature['properties']['model_cont']
    return features
