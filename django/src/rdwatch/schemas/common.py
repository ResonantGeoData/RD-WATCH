from ninja import Schema


class TimeRangeSchema(Schema):
    min: int | None
    max: int | None


class BoundingBoxSchema(Schema):
    xmin: float
    xmax: float
    ymin: float
    ymax: float
