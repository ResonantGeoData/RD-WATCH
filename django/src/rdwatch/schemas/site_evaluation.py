from datetime import datetime

from ninja import Schema
from pydantic import validator


class SiteEvaluationRequest(Schema):
    label: str | None
    geom: dict | None = None  # TODO: Replace with pydantics geoJSON
    score: float | None
    start_date: datetime | None
    end_date: datetime | None
    notes: str | None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')
