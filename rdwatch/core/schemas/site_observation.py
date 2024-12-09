from datetime import datetime

from ninja import Schema
from pydantic import field_validator


class SiteObservationRequest(Schema):
    label: str | None = None
    geom: dict | None = None  # TODO: Replace with pydantics geoJSON
    score: float | None = None
    timestamp: datetime
    constellation: str  # WV, S8, L8, PL
    spectrum: str | None = None
    notes: str | None = None

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')
