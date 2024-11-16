from datetime import datetime

from ninja import Schema
from pydantic import field_validator


class SiteObservationRequest(Schema):
    label: str | None
    geom: dict | None = None  # TODO: Replace with pydantics geoJSON
    score: float | None
    timestamp: datetime
    constellation: str  # WV, S8, L8, PL
    spectrum: str | None
    notes: str | None

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')
