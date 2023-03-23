# flake8: noqa: F722
import json
from datetime import datetime
from typing import Any, Literal

from ninja import Schema
from pydantic import constr, root_validator, validator

from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import GEOSGeometry


class SiteFeature(Schema):
    type: Literal['site']
    region_id: constr(regex=r'^[A-Z]{2}_[RCST][\dx]{3}$')
    site_id: str
    version: constr(regex=r'^\d+\.\d+\.\d+$')
    mgrs: constr(regex=r'^\d\d[A-Za-z]{3}$')
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
    model_content: Literal['annotation', 'proposed']
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
    score: float | None
    validated: Literal['True', 'False'] | None
    predicted_phase_transition: Literal[
        'Active Construction',
        'Post Construction',
    ] | None
    predicted_phase_transition_date: str | None
    misc_info: dict[Any, Any] | None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')

    @property
    def site_number(self) -> int:
        return int(self.site_id[8:])


class ObservationFeature(Schema):
    type: Literal['observation']
    observation_date: datetime | None
    source: str | None
    sensor_name: Literal['Landsat 8', 'Sentinel-2', 'WorldView', 'Planet'] | None
    current_phase: Literal[
        'No Activity',
        'Site Preparation',
        'Active Construction',
        'Post Construction',
        'Unknown',
    ]
    is_occluded: bool | None
    is_site_boundary: bool | None

    @validator('is_occluded', 'is_site_boundary', pre=True)
    def coerce_booleans(cls, val: Literal['True', 'False'] | bool | None):
        if val is None or isinstance(val, bool):
            return val
        return val != 'False'

    @validator('current_phase', pre=True)
    def convert_null_phases_to_unknown(cls, val: str | None):
        if val is None:
            return 'Unknown'
        return val

    @validator('observation_date', pre=True)
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')

    # Optional fields
    score: float | None
    misc_info: dict[Any, Any] | None


class Feature(Schema):
    class Config:
        arbitrary_types_allowed = True

    type: Literal['Feature']
    properties: SiteFeature | ObservationFeature
    geometry: GEOSGeometry

    @validator('geometry', pre=True)
    def parse_geometry(cls, v: dict[str, Any]):
        try:
            return GEOSGeometry(json.dumps(v))
        except GDALException:
            raise ValueError('Failed to parse geometry.')

    @root_validator
    def ensure_correct_geometry_type(cls, values: dict[str, Any]):
        if 'properties' not in values or 'geometry' not in values:
            return values
        if (
            isinstance(values['properties'], SiteFeature)
            and values['geometry'].geom_type != 'Polygon'
        ):
            raise ValueError('Site geometry must be of type "Polygon"')
        if (
            isinstance(values['properties'], ObservationFeature)
            and values['geometry'].geom_type != 'MultiPolygon'
        ):
            raise ValueError('Observation geometry must be of type "MultiPolygon"')
        return values


class SiteModel(Schema):
    type: Literal['FeatureCollection']
    features: list[Feature]

    @property
    def site_feature(self) -> Feature:
        return [
            feature
            for feature in self.features
            if isinstance(feature.properties, SiteFeature)
        ][0]

    @property
    def observation_features(self) -> list[Feature]:
        return [
            feature
            for feature in self.features
            if isinstance(feature.properties, ObservationFeature)
        ]

    @validator('features')
    def ensure_one_site_feature(cls, v: list[Feature]):
        site_features = [feature for feature in v if feature.properties.type == 'site']
        if len(site_features) != 1:
            raise ValueError("must contain exactly one 'Site' feature")
        return v

    @validator('features', pre=True)
    def preprocess_features(cls, v: list):
        return _preprocess_features(v)


def _preprocess_features(features: list) -> list:
    new_features = []
    for feature in features:
        if (
            feature['properties'].get('current_phase')
            and ', ' in feature['properties']['current_phase']
        ):
            affected_fields = (
                'current_phase',
                'is_occluded',
                'is_site_boundary',
            )
            for i, phase in enumerate(
                feature['properties']['current_phase'].split(', ')
            ):
                new_properties = {
                    **feature['properties'],
                    'geometry': {
                        'type': feature['geometry']['type'],
                        'coordinates': feature['geometry']['coordinates'][i],
                    },
                    **{
                        field: feature['properties'][field].split(', ')[i]
                        for field in affected_fields
                    },
                }
                new_feature = {**feature, 'properties': new_properties}
                new_features.append(new_feature)
        else:
            new_features.append(feature)
            continue
    return new_features
