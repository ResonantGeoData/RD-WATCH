# flake8: noqa: F722
import json
from datetime import datetime
from typing import Annotated, Any, Literal

from ninja import Field, Schema
from pydantic import confloat, constr, root_validator, validator

from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import GEOSGeometry


class SiteFeatureCache(Schema):
    originator_file: str
    timestamp: datetime | None
    commit_hash: str


class SiteFeature(Schema):
    type: Literal['site']
    region_id: constr(regex=r'^[A-Z]{2}_[RCST][\dx]{3}$')
    site_id: constr(regex=r'^[A-Z]{2}_([RST]\d{3}|C[0-7]\d{2}|[RC][Xx]{3})_\d{4,6}$')
    version: constr(regex=r'^\d+\.\d+\.\d+$')
    mgrs: constr(regex=r'^\d{2}[A-Z]{3}$')
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
    score: confloat(ge=0.0, le=1.0) | None
    validated: Literal['True', 'False'] | None
    cache: SiteFeatureCache | None
    predicted_phase_transition: Literal[
        'Active Construction',
        'Post Construction',
    ] | None
    predicted_phase_transition_date: str | None
    misc_info: dict[str, Any] | None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')

    @validator('score', pre=True, always=True)
    def parse_score(cls, v: float | None) -> float:
        """
        Score is an optional field, and defaults to 1.0 if one isn't provided
        https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification#score-float-optional
        """
        if v is None:
            return 1.0
        return v

    @property
    def site_number(self) -> int:
        return int(self.site_id[8:])


class ObservationFeature(Schema):
    type: Literal['observation']
    observation_date: datetime | None
    source: str | None
    sensor_name: Literal['Landsat 8', 'Sentinel-2', 'WorldView', 'Planet'] | None
    current_phase: list[
        Literal[
            'No Activity',
            'Site Preparation',
            'Active Construction',
            'Post Construction',
            'Unknown',
        ]
    ] | None
    is_occluded: list[bool] | None
    is_site_boundary: list[bool] | None

    @validator('is_occluded', 'is_site_boundary', pre=True)
    def convert_bools_to_list(cls, val: str, values, field):
        """
        Converts comma-space-seperated strings into lists of bools.
        """
        if val is None:
            return val
        converted_list = [
            {'True': True, 'False': False}.get(v, None) for v in val.split(', ')
        ]
        if None in converted_list:
            raise ValueError(
                f'Invalid value "{val}" for field {field.name} - '
                'must be a comma-space-separated formatted string.'
            )
        return converted_list

    @validator('current_phase', pre=True)
    def convert_phases_to_list(cls, val: str | None):
        """
        Converts comma-space-seperated strings into lists of phase strings.
        """
        if val is None:
            return val
        return val.split(', ')

    @validator('observation_date', pre=True)
    def parse_dates(cls, v: Any) -> datetime | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError('"observation_date" must be a valid date string.')
        return datetime.strptime(v, '%Y-%m-%d')

    @root_validator
    def ensure_consistent_list_lengths(cls, values: dict[str, Any]):
        lists = [
            values.get(field)
            for field in ('current_phase', 'is_occluded', 'is_site_boundary')
            if values.get(field) is not None
        ]
        if len(lists) and len({len(l) for l in lists}) != 1:
            raise ValueError(
                'current_phase/is_occluded/is_site_boundary lists must be the same length!'
            )
        return values

    # Optional fields
    score: confloat(ge=0.0, le=1.0) | None
    misc_info: dict[str, Any] | None

    @validator('score', pre=True, always=True)
    def parse_score(cls, v: float | None) -> float:
        """
        Score is an optional field, and defaults to 1.0 if one isn't provided
        https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification#score-float-optional-1
        """
        if v is None:
            return 1.0
        return v


class Feature(Schema):
    class Config:
        arbitrary_types_allowed = True

    type: Literal['Feature']
    properties: Annotated[
        SiteFeature | ObservationFeature,
        Field(discriminator='type'),
    ]
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
