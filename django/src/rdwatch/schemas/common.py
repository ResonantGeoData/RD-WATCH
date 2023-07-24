from ninja import Schema


class TimeRangeSchema(Schema):
    min: int
    max: int


class BoundingBoxSchema(Schema):
    xmin: float
    xmax: float
    ymin: float
    ymax: float
