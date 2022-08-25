from django.contrib.gis.db import models


class Site(models.Model):
    ACTIVE_CONSTRUCTION = "AC"
    POST_CONSTRUCTION = "PC"
    SITE_PREPARATION = "SP"
    LABEL_CHOICES = [
        (ACTIVE_CONSTRUCTION, "Active Construction"),
        (SITE_PREPARATION, "Site Preparation"),
        (POST_CONSTRUCTION, "Post Construction"),
    ]
    ground_truth = models.ForeignKey(
        "GroundTruth",
        related_name="sites",
        on_delete=models.CASCADE,
        help_text="The ground truth associated with this site.",
    )
    configuration = models.ForeignKey(
        to="TrackingConfiguration",
        on_delete=models.CASCADE,
        help_text="The tracking configuration this site was evaluated with",
    )
    saliency = models.ForeignKey(
        to="Saliency",
        on_delete=models.CASCADE,
        help_text="The saliency raster that was used to classify this site",
    )
    label = models.CharField(
        max_length=2,
        choices=LABEL_CHOICES,
        help_text="Site classification label",
    )
    score = models.FloatField(
        help_text="Evaluation accuracy",
    )
    geometry = models.MultiPolygonField(
        help_text="Footprint of site",
        srid=3857,
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
                fields=["configuration", "saliency", "label"],
                violation_error_message=(  # type: ignore
                    "Unique constraint invalid. Add polygons to existing site."
                ),
            ),
        ]
