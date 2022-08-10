# Generated by Django 4.1 on 2022-08-10 14:33

import django.contrib.gis.db.models.fields
import django.contrib.postgres.constraints
import django.contrib.postgres.indexes
import django.db.models.deletion
import django.db.models.lookups
import rdwatch.db.functions
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("rdwatch", "0001_initial")]

    operations = [
        BtreeGistExtension(),
        migrations.AlterField(
            model_name="predictionconfiguration",
            name="timestamp",
            field=models.DateTimeField(
                help_text=(
                    "Time when evaluating this prediction configuration was finished"
                )
            ),
        ),
        migrations.AlterField(
            model_name="saliency",
            name="configuration",
            field=models.ForeignKey(
                help_text=(
                    "The configuration profile used to generate this saliency map"
                ),
                on_delete=django.db.models.deletion.CASCADE,
                to="rdwatch.predictionconfiguration",
            ),
        ),
        migrations.AlterField(
            model_name="saliency",
            name="source",
            field=models.ForeignKey(
                help_text=(
                    "The source satellite imagery this saliency map was evaluated on"
                ),
                on_delete=django.db.models.deletion.PROTECT,
                to="rdwatch.satelliteimage",
            ),
        ),
        migrations.AlterField(
            model_name="saliencytile",
            name="raster",
            field=django.contrib.gis.db.models.fields.RasterField(
                help_text="A 64x64 single-band tile from the full saliency map",
                srid=4326,
            ),
        ),
        migrations.AlterField(
            model_name="saliencytile",
            name="saliency",
            field=models.ForeignKey(
                help_text="The saliency map this tile belongs to",
                on_delete=django.db.models.deletion.CASCADE,
                to="rdwatch.saliency",
            ),
        ),
        migrations.AlterField(
            model_name="satelliteimage",
            name="sensor",
            field=models.CharField(
                choices=[("L8", "Landsat 8"), ("S2", "Sentinel 2")],
                help_text="The source satellite sensor",
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="satelliteimage",
            name="timestamp",
            field=models.DateTimeField(
                help_text="The time the source imagery was captured"
            ),
        ),
        migrations.AlterField(
            model_name="site",
            name="configuration",
            field=models.ForeignKey(
                help_text="The tracking configuration this site was evaluated with",
                on_delete=django.db.models.deletion.CASCADE,
                to="rdwatch.trackingconfiguration",
            ),
        ),
        migrations.AlterField(
            model_name="site",
            name="geometry",
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                help_text="Footprint of site", srid=4326
            ),
        ),
        migrations.AlterField(
            model_name="site",
            name="label",
            field=models.CharField(
                choices=[("AC", "Active Construction"), ("SP", "Site Preperation")],
                help_text="Site classification label",
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="site",
            name="saliency",
            field=models.ForeignKey(
                help_text="The saliency raster that was used to classify this site",
                on_delete=django.db.models.deletion.CASCADE,
                to="rdwatch.saliency",
            ),
        ),
        migrations.AlterField(
            model_name="site",
            name="score",
            field=models.FloatField(help_text="Evaluation accuracy"),
        ),
        migrations.AlterField(
            model_name="trackingconfiguration",
            name="threshold",
            field=models.FloatField(help_text="Threshold for tracking site in time"),
        ),
        migrations.AlterField(
            model_name="trackingconfiguration",
            name="timestamp",
            field=models.DateTimeField(
                help_text=(
                    "Time when evaluating this tracking configuration was finished"
                )
            ),
        ),
        migrations.AddIndex(
            model_name="predictionconfiguration",
            index=models.Index(
                fields=["timestamp"], name="rdwatch_pre_timesta_bfca81_idx"
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
        migrations.AddIndex(
            model_name="site",
            index=models.Index(
                fields=["configuration"], name="rdwatch_sit_configu_294d82_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="site",
            index=models.Index(
                fields=["saliency"], name="rdwatch_sit_salienc_f809e3_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="site",
            index=models.Index(fields=["label"], name="rdwatch_sit_label_2af553_idx"),
        ),
        migrations.AddIndex(
            model_name="site",
            index=models.Index(fields=["score"], name="rdwatch_sit_score_5b4215_idx"),
        ),
        migrations.AddIndex(
            model_name="site",
            index=models.Index(
                fields=["geometry"], name="rdwatch_sit_geometr_7ad672_idx"
            ),
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
        migrations.AddConstraint(
            model_name="saliencytile",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[
                    (
                        django.contrib.postgres.indexes.OpClass(
                            rdwatch.db.functions.RasterEnvelope("raster"),
                            name="gist_geometry_ops_2d",
                        ),
                        "&&",
                    ),
                    ("saliency", "="),
                ],
                name="exclude_overlapping_raster",
                violation_error_message=(
                    "Tiles for the same raster cannot overlap"
                ),  # type: ignore
            ),
        ),
        migrations.AddConstraint(
            model_name="saliencytile",
            constraint=models.CheckConstraint(
                check=django.db.models.lookups.Exact(
                    rdwatch.db.functions.RasterHeight("raster"), 64
                ),  # type: ignore
                name="check_64_height_raster",
                violation_error_message="Tile must be 64 pixels high",  # type: ignore
            ),
        ),
        migrations.AddConstraint(
            model_name="saliencytile",
            constraint=models.CheckConstraint(
                check=django.db.models.lookups.Exact(
                    rdwatch.db.functions.RasterWidth("raster"), 64
                ),  # type: ignore
                name="check_64_width_raster",
                violation_error_message="Tile must be 64 pixels wide",  # type: ignore
            ),
        ),
        migrations.AddConstraint(
            model_name="saliencytile",
            constraint=models.CheckConstraint(
                check=django.db.models.lookups.Exact(
                    rdwatch.db.functions.RasterNumBands("raster"), 1
                ),  # type: ignore
                name="check_1_band_raster",
                violation_error_message="Tile must only have one band",  # type: ignore
            ),
        ),
        migrations.AddConstraint(
            model_name="satelliteimage",
            constraint=models.UniqueConstraint(
                fields=("sensor", "timestamp"),
                name="unique_satelliteimage",
                violation_error_message=("Satellite image already exists.",),
            ),  # type: ignore
        ),
        migrations.AddConstraint(
            model_name="site",
            constraint=models.UniqueConstraint(
                fields=("configuration", "saliency", "label"),
                name="unique_configuration_saliency_label",
                violation_error_message=(
                    "Unique constraint invalid. Add polygons to existing site.",
                ),  # type: ignore
            ),
        ),
    ]
