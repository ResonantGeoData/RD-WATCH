import iso3166

from django.db import models

from rdwatch.validators import validate_iso3166


class Region(models.Model):
    country = models.PositiveSmallIntegerField(
        help_text="The numeric country identifier as specified by ISO 3166",
        db_index=True,
        validators=[validate_iso3166],
    )
    classification = models.ForeignKey(
        to="RegionClassification",
        on_delete=models.PROTECT,
        help_text="Region classification code",
        db_index=True,
    )
    number = models.PositiveSmallIntegerField(
        help_text="The region number",
        db_index=True,
    )

    def __str__(self):
        cty = iso3166.countries_by_numeric[str(self.country).zfill(3)].alpha2
        rcls = self.classification.slug
        num = str(self.number).zfill(3)
        return f"{cty}_{rcls}{num}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="uniq_region",
                fields=[
                    "country",
                    "classification",
                    "number",
                ],
                violation_error_message="Region already exists.",  # type: ignore
            ),
        ]
