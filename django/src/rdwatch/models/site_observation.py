from django.contrib.gis.db import models


class SiteObservation(models.Model):
    ACTIVE_CONSTRUCTION = "AC"
    POST_CONSTRUCTION = "PC"
    SITE_PREPARATION = "SP"
    LABEL_CHOICES = [
        (ACTIVE_CONSTRUCTION, "Active Construction"),
        (SITE_PREPARATION, "Site Preparation"),
        (POST_CONSTRUCTION, "Post Construction"),
    ]
    site = models.ForeignKey(
        to="Site",
        related_name="observations",
        on_delete=models.CASCADE,
        help_text="The site associated with this observation.",
    )
    configuration = models.ForeignKey(
        to="TrackingConfiguration",
        on_delete=models.CASCADE,
        help_text="The tracking configuration this site was evaluated with",
    )
    saliency = models.ForeignKey(
        to="Saliency",
        on_delete=models.CASCADE,
        help_text="The saliency raster that was used to classify this site observation",
    )
    label = models.CharField(
        max_length=2,
        choices=LABEL_CHOICES,
        help_text="Site observation classification label",
    )
    score = models.FloatField(
        help_text="Evaluation accuracy",
    )
    geometry = models.MultiPolygonField(
        help_text="Footprint of site observation",
        srid=3857,
    )
    band = models.CharField(
        max_length=20,
        help_text="The satellite imagery band used to refine this observation",
    )

    def __str__(self):
        return f"Site:{self.pk}"

    class Meta:
        indexes = [
            models.Index(fields=["configuration"]),
            models.Index(fields=["saliency"]),
            models.Index(fields=["label"]),
            models.Index(fields=["score"]),
            models.Index(fields=["geometry"]),
        ]
        constraints = [
            models.UniqueConstraint(
                name="unique_configuration_saliency_label",
                fields=["site", "configuration", "saliency", "label", "score", "band"],
                violation_error_message=(  # type: ignore
                    "Unique constraint invalid. Add polygons to existing site."
                ),
            ),
        ]
