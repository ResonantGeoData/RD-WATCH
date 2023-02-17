# flake8: noqa: F722
import json
from typing import Any, Literal

from pydantic import BaseModel, constr, validator

from django.contrib.gis.geos import GEOSGeometry


class RegionFeature(BaseModel):
    type: Literal['region']
    region_id: constr(regex=r'^[A-Z]{2}_[RCST]\d{3}$')
    version: str | None
    mgrs: str
    model_content: Literal['empty', 'annotation', 'proposed'] | None
    start_date: str | None
    end_date: str | None
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


class SiteSummaryFeature(BaseModel):
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
    start_date: str | None
    end_date: str | None
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


class Feature(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    type: Literal['Feature']
    properties: RegionFeature | SiteSummaryFeature
    geometry: GEOSGeometry

    @validator('geometry', pre=True)
    def parse_geometry(cls, v: dict[str, Any]):
        return GEOSGeometry(json.dumps(v))


class RegionModel(BaseModel):
    type: Literal['FeatureCollection']
    features: list[Feature]

    @validator('features', pre=True)
    def preprocess_features(cls, v: list):
        return _preprocess_features(v)


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
