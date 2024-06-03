from django.contrib.gis.db.models import PolygonField
from django.contrib.gis.geos import Polygon
from django.db import models, transaction


class Region(models.Model):
    name = models.CharField(max_length=255)
    geom = PolygonField(
        help_text='Polygon from the associated Region Feature',
        srid=3857,
        spatial_index=True,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='uniq_region',
                fields=['name'],
                violation_error_message='Region already exists.',  # type: ignore
            ),
        ]


def get_or_create_region(
    region_id: str,
    region_polygon: Polygon | None = None,
) -> tuple[Region, bool]:
    with transaction.atomic():
        region, created = Region.objects.select_for_update().get_or_create(
            name=region_id
        )
        if region.geom is None and region_polygon is not None:
            region.geom = region_polygon
            region.save()
        return region, created
