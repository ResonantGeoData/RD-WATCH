# flake8: noqa: F722
import json
from datetime import datetime
from typing import Annotated, Any, Literal

from ninja import Field, Schema
from pydantic import Field, StringConstraints, field_validator

from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import GEOSGeometry, Polygon


class RegionFeature(Schema):
    type: Literal['region']
    region_id: str  # a Region isn't limited to their format for RDWATCH
    version: str | None = None
    mgrs: str
    model_content: Literal['empty', 'annotation', 'proposed'] | None = None
    start_date: datetime | None = Field(default=None, validate_default=True)
    end_date: datetime | None = Field(default=None, validate_default=True)
    originator: str

    # Optional fields
    comments: str | None = None
    performer_cache: dict[Any, Any] | None = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')


class SiteSummaryFeature(Schema):
    type: Literal['site_summary']
    # match the site_id of format KR_R001_0001 or KR_R001_9990
    site_id: Annotated[str, StringConstraints(pattern=r'^.{1,255}_\d{4,8}$')]
    version: str | None = None
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
    start_date: datetime | None = Field(default=None, validate_default=True)
    end_date: datetime | None = Field(default=None, validate_default=True)
    model_content: Literal['annotation', 'proposed'] | None = None
    originator: str

    # Optional fields
    comments: str | None = None
    score: Annotated[float, Field(ge=0.0, le=1.0)] | None = Field(
        default=None, validate_default=True
    )
    validated: Literal['True', 'False'] | None = None
    annotation_cache: dict[Any, Any] | None = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')

    @field_validator('score', mode='before')
    @classmethod
    def parse_score(cls, v: float | None) -> float:
        """
        Score is an optional field, and defaults to 1.0 if one isn't provided
        https://smartgitlab.com/TE/standards/-/wikis/Region-Model-Specification#score-float-optional
        """
        return v if v is not None else 1.0

    @property
    def site_number(self) -> int:
        splits = self.site_id.split('_')
        return int(splits[-1])


class Feature(Schema):
    type: Literal['Feature']
    properties: Annotated[
        RegionFeature | SiteSummaryFeature,
        Field(discriminator='type'),
    ]
    geometry: dict[str, Any]

    @property
    def parsed_geometry(self) -> GEOSGeometry:
        return GEOSGeometry(json.dumps(self.geometry))

    @field_validator('geometry', mode='before')
    def parse_geometry(cls, v: dict[str, Any]) -> dict[str, Any]:
        try:
            geom = GEOSGeometry(json.dumps(v))
            if not isinstance(geom, Polygon):
                raise ValueError('A region or site summary geometry must be a Polygon.')
            return v
        except GDALException:
            raise ValueError('Failed to parse geometry.')


class RegionModel(Schema):
    type: Literal['FeatureCollection']
    features: list[Feature]

    @field_validator('features')
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
