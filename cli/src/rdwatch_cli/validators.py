import click


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
