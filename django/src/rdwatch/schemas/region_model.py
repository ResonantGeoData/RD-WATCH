# flake8: noqa: F722
import json
from datetime import datetime
from typing import Annotated, Any, Literal

from ninja import Field, Schema
from pydantic import confloat, constr, validator

from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import GEOSGeometry, Polygon


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
    # match the site_id of format KR_R001_0001 or KR_R001_9990
    site_id: constr(regex=r'^[A-Z]{2}_[RCST]\d{3}_\d{4,8}$')
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
    score: confloat(ge=0.0, le=1.0) | None
    validated: Literal['True', 'False'] | None
    annotation_cache: dict[Any, Any] | None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')

    @validator('score', pre=True, always=True)
    def parse_score(cls, v: float | None) -> float:
        """
        Score is an optional field, and defaults to 1.0 if one isn't provided
        https://smartgitlab.com/TE/standards/-/wikis/Region-Model-Specification#score-float-optional
        """
        if v is None:
            return 1.0
        return v

    @property
    def site_number(self) -> int:
        return int(self.site_id[8:])


class Feature(Schema):
    class Config:
        arbitrary_types_allowed = True

    type: Literal['Feature']
    properties: Annotated[
        RegionFeature | SiteSummaryFeature,
        Field(discriminator='type'),
    ]
    geometry: Polygon

    @validator('geometry', pre=True)
    def parse_geometry(cls, v: dict[str, Any]):
        try:
            geom = GEOSGeometry(json.dumps(v))
            if not isinstance(geom, Polygon):
                raise ValueError('A region or site summary geometry must be a Polygon.')
            return geom
        except GDALException:
            raise ValueError('Failed to parse geometry.')


class RegionModel(Schema):
    type: Literal['FeatureCollection']
    features: list[Feature]

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
