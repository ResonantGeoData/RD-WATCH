import json

from django.contrib.auth.models import User
from django.contrib.gis.db.models import PolygonField
from django.contrib.gis.geos import Polygon
from django.db import models, transaction
from django.db.models import Q

from rdwatch.core.schemas import RegionModel
from rdwatch.core.schemas.region_model import RegionFeature


class Region(models.Model):
    name = models.CharField(max_length=255)
    geom = PolygonField(
        help_text='Polygon from the associated Region Feature',
        srid=3857,
        spatial_index=True,
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    public = models.BooleanField(default=True)

    @property
    def value(self):
        if self.owner:
            return f'{self.name}_{self.owner.username}'
        return self.name

    @property
    def bounding_box(self):
        if self.geom:
            return self.geom.extent  # Returns (xmin, ymin, xmax, ymax)
        return None

    @property
    def geojson(self):
        if self.geom:
            geom_transformed = self.geom.transform(
                4326, clone=True
            )  # Ensure it's in WGS 84
            return json.loads(
                geom_transformed.geojson
            )  # Convert GeoJSON string to dictionary
        return None

    def __str__(self) -> str:
        return self.name

    def to_feature(self):
        return {
            'type': 'Feature',
            'properties': {
                'type': 'region',
                'region_id': self.name,
                'version': '2.0.3',
                'mgrs': None,  # or other logic to populate this field
                'start_date': None,  # or other logic to populate this field
                'end_date': None,  # or other logic to populate this field
                'originator': 'kit',  # or other logic to populate this field
                'model_content': 'annotation',  # or other logic to populate this field
                'comments': None,  # or other logic to populate this field
            },
            'geometry': {
                'type': 'Polygon',
                'coordinates': self.geom.coords if self.geom else None,
            },
        }

    def to_feature_collection(self):
        return {'type': 'FeatureCollection', 'features': [self.to_feature()]}

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_region_with_null_owner',
                fields=['name'],
                condition=Q(owner__isnull=True),
                violation_error_message='Region already exists with a null owner.',
            ),
            models.UniqueConstraint(
                name='unique_region_with_owner',
                fields=['name', 'owner'],
                condition=Q(owner__isnull=False),
                violation_error_message='Region already exists with \
                    this name and owner.',
            ),
        ]

    @classmethod
    def create_region_model_from_geoJSON(
        cls, region_model: RegionModel, public=False, owner=None
    ):
        region_feature = region_model.region_feature
        assert isinstance(region_feature.properties, RegionFeature)
        return get_or_create_region(
            region_feature.properties.region_id,
            region_feature.parsed_geometry,
            public,
            owner,
        )


def get_or_create_region(
    region_id: str,
    region_polygon: Polygon | None = None,
    public: bool = False,
    owner: int | None = None,
) -> tuple[Region, bool]:
    with transaction.atomic():
        region, created = Region.objects.select_for_update().get_or_create(
            name=region_id
        )
        if region.geom is None and region_polygon is not None:
            region.geom = region_polygon
            if public:
                region.public = public
            if owner:
                region.owner = owner
            region.save()
        return region, created
