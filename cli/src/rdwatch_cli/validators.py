from datetime import datetime

import click


def validate_timestamp(ctx, param, value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise click.BadParameter("invalid isoformat string")


def validate_timestamps(ctx, param, value):
    return tuple(validate_timestamp(ctx, param, v) for v in value)


def validate_bbox(ctx, param, value):
    if not len(value) == 4:
        raise click.BadParameter("invalid bbox")
    bbox = tuple(float(x) for x in value)
    if (
        not bbox[0] < bbox[2]
        or not bbox[1] < bbox[3]
        or bbox[0] < -180
        or bbox[2] > 180
        or bbox[1] < -90
        or bbox[3] > 90
    ):
        raise click.BadParameter("invalid bbox")
    return bbox
