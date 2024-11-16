# flake8: noqa: F722
import json
from datetime import datetime
from typing import Annotated, Any, Literal, TypeAlias

from ninja import Field, Schema
from pydantic import Field, StringConstraints, field_validator, model_validator

from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException

CurrentPhase: TypeAlias = Literal[
    'No Activity',
    'Site Preparation',
    'Active Construction',
    'Post Construction',
    'Unknown',
]


class SiteFeatureCache(Schema):
    originator_file: str | None
    timestamp: datetime | None
    commit_hash: str | None


class SiteFeature(Schema):
    type: Literal['site']
    region_id: Annotated[str, StringConstraints(min_length=1, max_length=255)]
    site_id: Annotated[str, StringConstraints(pattern=r'^.{1,255}_\d{4,8}$')]
    version: Annotated[str, StringConstraints(pattern=r'^\d+\.\d+\.\d+$')]
    mgrs: Annotated[str, StringConstraints(pattern=r'^\d{2}[A-Z]{3}$')]
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
    model_content: Literal['annotation', 'proposed', 'update']
    originator: str

    # Optional fields
    score: Annotated[float, Field(ge=0.0, le=1.0)] | None = None
    validated: Literal['True', 'False'] | None = None
    cache: SiteFeatureCache | None = None
    predicted_phase_transition: (
        Literal[
            'Active Construction',
            'Post Construction',
        ]
        | None
    )
    predicted_phase_transition_date: str | None = None
    misc_info: dict[str, Any] | None = None

    @field_validator('start_date', 'end_date', mode='before')
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')

    @field_validator('score', mode='before')
    def parse_score(cls, v: float | None) -> float:
        """
        Score is an optional field, and defaults to 1.0 if one isn't provided
        https://smartgitlab.com/TE/standards/-/wikis/Site-Model-Specification#score-float-optional
        """
        return v if v is not None else 1.0

    @property
    def site_number(self) -> int:
        splits = self.site_id.split('_')
        return int(splits[-1])


class ObservationFeature(Schema):
    type: Literal['observation']
    observation_date: datetime | None
    source: str | None
    sensor_name: Literal['Landsat 8', 'Sentinel-2', 'WorldView', 'Planet'] | None
    current_phase: list[CurrentPhase] | None = None
    is_occluded: list[bool] | None = None
    is_site_boundary: list[bool] | None = None

    @field_validator('is_occluded', 'is_site_boundary', mode='before')
    def convert_bools_to_list(cls, val: str | None):
        """
        Converts comma-space-separated strings into lists of bools.
        """
        if val is None:
            return val
        converted_list = [
            {'True': True, 'False': False}.get(v, None) for v in val.split(', ')
        ]
        if None in converted_list:
            raise ValueError(
                f'Invalid value "{val}" - must be a comma-space-separated formatted string.'
            )
        return converted_list

    @field_validator('current_phase', mode='before')
    def convert_phases_to_list(cls, val: str | None):
        """
        Converts comma-space-separated strings into lists of phase strings.
        """
        if val is None:
            return val
        return val.split(', ')

    @field_validator('observation_date', mode='before')
    def parse_dates(cls, v: Any) -> datetime | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError('"observation_date" must be a valid date string.')
        return datetime.strptime(v, '%Y-%m-%d')

    @model_validator(mode='after')
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
    score: Annotated[float, Field(ge=0.0, le=1.0)] | None = None
    misc_info: dict[str, Any] | None = None

    @field_validator('score', mode='before')
    def parse_score(cls, v: float | None) -> float:
        """
        Score is an optional field, and defaults to 1.0 if one isn't provided
        """
        return v if v is not None else 1.0


class Feature(Schema):
    type: Literal['Feature']
    properties: Annotated[
        SiteFeature | ObservationFeature,
        Field(discriminator='type'),
    ]
    geometry: dict[str, Any]

    @property
    def parsed_geometry(self) -> GEOSGeometry:
        return GEOSGeometry(json.dumps(self.geometry))

    @field_validator('geometry', mode='before')
    def parse_geometry(cls, v: dict[str, Any]):
        try:
            GEOSGeometry(json.dumps(v))
        except GDALException:
            raise ValueError('Failed to parse geometry.')
        except GEOSException as e:
            raise ValueError(f'Failed to parse geometry: {e}')
        return v

    @model_validator(mode='after')
    def ensure_correct_geometry_type(cls, values: dict[str, Any]):
        if 'properties' not in values or 'geometry' not in values:
            return values
        if isinstance(values['properties'], SiteFeature) and (
            values['geometry'].get('type') not in ['Polygon', 'Point']
        ):
            raise ValueError('Site geometry must be of type "Polygon" or "Point"')
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

    @field_validator('features')
    def ensure_one_site_feature(cls, v: list[Feature]):
        site_features = [feature for feature in v if feature.properties.type == 'site']
        if len(site_features) != 1:
            raise ValueError("must contain exactly one 'Site' feature")
        return v
