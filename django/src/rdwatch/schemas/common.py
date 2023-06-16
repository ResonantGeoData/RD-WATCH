from ninja import Schema


class TimeRangeSchema(Schema):
    min: int
    max: int
