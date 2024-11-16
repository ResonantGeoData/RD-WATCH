from datetime import datetime
from typing import Literal

from ninja import Schema
from pydantic import field_validator


class SiteEvaluationRequest(Schema):
    label: str | None = None
    geom: dict | None = None
    score: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    notes: str | None = None
    status: Literal['PROPOSAL', 'APPROVED', 'REJECTED'] | None = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_dates(cls, v: str | None) -> datetime | None:
        if v is None:
            return v
        return datetime.strptime(v, '%Y-%m-%d')
