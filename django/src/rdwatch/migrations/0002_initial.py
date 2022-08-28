# type: ignore
# flake8: noqa
import django.contrib.gis.db.models.fields
import django.contrib.postgres.constraints
import django.db.models.deletion
import django.db.models.lookups
import rdwatch.db.functions
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("rdwatch", "0001_extensions"),
    ]

    operations = [
        migrations.CreateModel(
            name="PredictionConfiguration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slug", models.SlugField(max_length=8)),
                (
                    "timestamp",
                    models.DateTimeField(
                        help_text="Time when evaluating this prediction configuration was finished"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Saliency",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SaliencyTile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "raster",
                    django.contrib.gis.db.models.fields.RasterField(
                        help_text="A 64x64 single-band tile from the full saliency map",
                        srid=3857,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SatelliteImage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "sensor",
                    models.CharField(
                        choices=[("L8", "Landsat 8"), ("S2", "Sentinel 2")],
                        help_text="The source satellite sensor",
                        max_length=2,
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        help_text="The time the source imagery was captured"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Site",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "geometry",
                    django.contrib.gis.db.models.fields.PolygonField(
                        help_text="Footprint of site", srid=3857
                    ),
                ),
                ("score", models.FloatField(help_text="Score of site footprint")),
            ],
        ),
        migrations.CreateModel(
            name="SiteObservation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        choices=[
                            ("AC", "Active Construction"),
                            ("SP", "Site Preparation"),
                            ("PC", "Post Construction"),
                        ],
                        help_text="Site observation classification label",
                        max_length=2,
                    ),
                ),
                ("score", models.FloatField(help_text="Evaluation accuracy")),
                (
                    "geometry",
                    django.contrib.gis.db.models.fields.MultiPolygonField(
                        help_text="Footprint of site observation", srid=3857
                    ),
                ),
                (
                    "band",
                    models.CharField(
                        help_text="The satellite imagery band used to refine this observation",
                        max_length=20,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TrackingConfiguration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        help_text="Time when evaluating this tracking configuration was finished"
                    ),
                ),
                ("slug", models.SlugField(max_length=8)),
                (
                    "threshold",
                    models.FloatField(help_text="Threshold for tracking site in time"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="trackingconfiguration",
            index=models.Index(fields=["slug"], name="rdwatch_tra_slug_006bcb_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingconfiguration",
            index=models.Index(
                fields=["timestamp"], name="rdwatch_tra_timesta_834bdb_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="trackingconfiguration",
            index=models.Index(
                fields=["threshold"], name="rdwatch_tra_thresho_650ab2_idx"
            ),
        ),
        migrations.AddField(
            model_name="siteobservation",
            name="configuration",
            field=models.ForeignKey(
                help_text="The tracking configuration this site was evaluated with",
                on_delete=django.db.models.deletion.CASCADE,
                to="rdwatch.trackingconfiguration",
            ),
        ),
        migrations.AddField(
            model_name="siteobservation",
            name="saliency",
            field=models.ForeignKey(
                help_text="The saliency raster that was used to classify this site observation",
                on_delete=django.db.models.deletion.CASCADE,
                to="rdwatch.saliency",
            ),
        ),
        migrations.AddField(
            model_name="siteobservation",
            name="site",
            field=models.ForeignKey(
                help_text="The site associated with this observation.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="observations",
                to="rdwatch.site",
            ),
        ),
        migrations.AddIndex(
            model_name="site",
            index=models.Index(
                fields=["geometry"], name="rdwatch_sit_geometr_7ad672_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="site",
            index=models.Index(fields=["score"], name="rdwatch_sit_score_5b4215_idx"),
        ),
        migrations.AddIndex(
            model_name="satelliteimage",
            index=models.Index(fields=["sensor"], name="rdwatch_sat_sensor_b2bdea_idx"),
        ),
        migrations.AddIndex(
            model_name="satelliteimage",
            index=models.Index(
                fields=["timestamp"], name="rdwatch_sat_timesta_c75900_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="satelliteimage",
            constraint=models.UniqueConstraint(
                fields=("sensor", "timestamp"),
                name="unique_satelliteimage",
                violation_error_message="Satellite image already exists.",
            ),
        ),
        migrations.AddField(
            model_name="saliencytile",
            name="saliency",
            field=models.ForeignKey(
                help_text="The saliency map this tile belongs to",
                on_delete=django.db.models.deletion.CASCADE,
                to="rdwatch.saliency",
            ),
        ),
        migrations.AddField(
            model_name="saliency",
            name="configuration",
            field=models.ForeignKey(
                help_text="The configuration profile used to generate this saliency map",
                on_delete=django.db.models.deletion.CASCADE,
                to="rdwatch.predictionconfiguration",
            ),
        ),
        migrations.AddField(
            model_name="saliency",
            name="source",
            field=models.ForeignKey(
                help_text="The source satellite imagery this saliency map was evaluated on",
                on_delete=django.db.models.deletion.PROTECT,
                to="rdwatch.satelliteimage",
            ),
        ),
        migrations.AddIndex(
            model_name="predictionconfiguration",
            index=models.Index(fields=["slug"], name="rdwatch_pre_slug_018439_idx"),
        ),
        migrations.AddIndex(
            model_name="predictionconfiguration",
            index=models.Index(
                fields=["timestamp"], name="rdwatch_pre_timesta_bfca81_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="siteobservation",
            index=models.Index(
                fields=["configuration"], name="rdwatch_sit_configu_3917f1_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="siteobservation",
            index=models.Index(
                fields=["saliency"], name="rdwatch_sit_salienc_b36893_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="siteobservation",
            index=models.Index(fields=["label"], name="rdwatch_sit_label_5fe73e_idx"),
        ),
        migrations.AddIndex(
            model_name="siteobservation",
            index=models.Index(fields=["score"], name="rdwatch_sit_score_355503_idx"),
        ),
        migrations.AddIndex(
            model_name="siteobservation",
            index=models.Index(
                fields=["geometry"], name="rdwatch_sit_geometr_baeb78_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="siteobservation",
            constraint=models.UniqueConstraint(
                fields=("site", "configuration", "saliency", "label", "score", "band"),
                name="unique_configuration_saliency_label",
                violation_error_message="Unique constraint invalid. Add polygons to existing site.",
            ),
        ),
        migrations.AddIndex(
            model_name="saliencytile",
            index=models.Index(fields=["raster"], name="rdwatch_sal_raster_202255_idx"),
        ),
        migrations.AddIndex(
            model_name="saliencytile",
            index=models.Index(
                fields=["saliency"], name="rdwatch_sal_salienc_8c7a07_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="saliencytile",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[
                    (rdwatch.db.functions.RasterXRange("raster"), "&&"),
                    (rdwatch.db.functions.RasterYRange("raster"), "&&"),
                    ("saliency", "="),
                ],
                name="exclude_overlapping_raster",
                violation_error_message="Tiles for the same raster cannot overlap",
            ),
        ),
        migrations.AddConstraint(
            model_name="saliencytile",
            constraint=models.CheckConstraint(
                check=django.db.models.lookups.Exact(
                    rdwatch.db.functions.RasterHeight("raster"), 64
                ),
                name="check_64_height_raster",
                violation_error_message="Tile must be 64 pixels high",
            ),
        ),
        migrations.AddConstraint(
            model_name="saliencytile",
            constraint=models.CheckConstraint(
                check=django.db.models.lookups.Exact(
                    rdwatch.db.functions.RasterWidth("raster"), 64
                ),
                name="check_64_width_raster",
                violation_error_message="Tile must be 64 pixels wide",
            ),
        ),
        migrations.AddConstraint(
            model_name="saliencytile",
            constraint=models.CheckConstraint(
                check=django.db.models.lookups.Exact(
                    rdwatch.db.functions.RasterNumBands("raster"), 1
                ),
                name="check_1_band_raster",
                violation_error_message="Tile must only have one band",
            ),
        ),
        migrations.AddIndex(
            model_name="saliency",
            index=models.Index(
                fields=["configuration"], name="rdwatch_sal_configu_49f83d_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="saliency",
            index=models.Index(
                fields=["source"], name="rdwatch_sal_source__8efd8a_idx"
            ),
        ),
    ]
