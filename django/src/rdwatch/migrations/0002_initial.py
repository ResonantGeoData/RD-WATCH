# flake8: noqa
# type: ignore

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.ranges
import django.contrib.postgres.indexes
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import rdwatch.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("rdwatch", "0001_extensions"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommonBand",
            fields=[
                ("id", models.SmallAutoField(primary_key=True, serialize=False)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField()),
                (
                    "spectrum",
                    django.contrib.postgres.fields.ranges.DecimalRangeField(
                        db_index=True, help_text="The spectrum this band captures (μm)"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Constellation",
            fields=[
                ("id", models.SmallAutoField(primary_key=True, serialize=False)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="HyperParameters",
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
                    "parameters",
                    models.JSONField(
                        db_index=True, help_text="The hyper parameters for an ML task"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ObservationLabel",
            fields=[
                ("id", models.SmallAutoField(primary_key=True, serialize=False)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Performer",
            fields=[
                ("id", models.SmallAutoField(primary_key=True, serialize=False)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProcessingLevel",
            fields=[
                ("id", models.SmallAutoField(primary_key=True, serialize=False)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Region",
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
                    "country",
                    models.PositiveSmallIntegerField(
                        db_index=True,
                        help_text="The numeric country identifier as specified by ISO 3166",
                        validators=[rdwatch.validators.validate_iso3166],
                    ),
                ),
                (
                    "number",
                    models.PositiveSmallIntegerField(
                        db_index=True, help_text="The region number"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RegionClassification",
            fields=[
                ("id", models.SmallAutoField(primary_key=True, serialize=False)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SiteEvaluation",
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
                    "number",
                    models.PositiveSmallIntegerField(
                        db_index=True, help_text="The site number"
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        help_text="Time when this evaluation was finished"
                    ),
                ),
                (
                    "geom",
                    django.contrib.gis.db.models.fields.PolygonField(
                        help_text="Footprint of site", srid=3857
                    ),
                ),
                ("score", models.FloatField(help_text="Score of site footprint")),
                (
                    "configuration",
                    models.ForeignKey(
                        help_text="The hyper parameters used this site evaluation.",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="rdwatch.hyperparameters",
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        help_text="The region this site belongs to",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="rdwatch.region",
                    ),
                ),
            ],
            options={
                "default_related_name": "evaluations",
            },
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
                ("score", models.FloatField(help_text="Evaluation accuracy")),
                (
                    "geom",
                    django.contrib.gis.db.models.fields.MultiPolygonField(
                        help_text="Footprint of site observation", srid=3857
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(help_text="The source image's timestamp"),
                ),
                (
                    "constellation",
                    models.ForeignKey(
                        help_text="The source image's satellite constellation",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="rdwatch.constellation",
                    ),
                ),
                (
                    "label",
                    models.ForeignKey(
                        help_text="Site observation classification label",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="rdwatch.observationlabel",
                    ),
                ),
                (
                    "siteeval",
                    models.ForeignKey(
                        help_text="The site evaluation associated with this observation.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="rdwatch.siteevaluation",
                    ),
                ),
                (
                    "spectrum",
                    models.ForeignKey(
                        help_text="The source image's satellite spectrum",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="rdwatch.commonband",
                    ),
                ),
            ],
            options={
                "default_related_name": "observations",
            },
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
                    "timestamp",
                    models.DateTimeField(help_text="The time the imagery was captured"),
                ),
                (
                    "bbox",
                    django.contrib.gis.db.models.fields.PolygonField(
                        help_text="The spatial extent of the image",
                        srid=3857,
                        validators=[rdwatch.validators.validate_bbox],
                    ),
                ),
                (
                    "uri",
                    models.CharField(
                        help_text="The URI of the raster",
                        max_length=200,
                        unique=True,
                        validators=[
                            django.core.validators.URLValidator(
                                schemes=["http", "https", "s3"]
                            )
                        ],
                    ),
                ),
                (
                    "constellation",
                    models.ForeignKey(
                        help_text="The source satellite constellation",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="rdwatch.constellation",
                    ),
                ),
                (
                    "level",
                    models.ForeignKey(
                        help_text="The processing level of the imagery",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="rdwatch.processinglevel",
                    ),
                ),
                (
                    "spectrum",
                    models.ForeignKey(
                        help_text="The spectrum range this raster captures",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="rdwatch.commonband",
                    ),
                ),
            ],
            options={
                "default_related_name": "satellite_images",
            },
        ),
        migrations.AddField(
            model_name="region",
            name="classification",
            field=models.ForeignKey(
                help_text="Region classification code",
                on_delete=django.db.models.deletion.PROTECT,
                to="rdwatch.regionclassification",
            ),
        ),
        migrations.AddField(
            model_name="hyperparameters",
            name="performer",
            field=models.ForeignKey(
                help_text="The team that produced this evaluation",
                on_delete=django.db.models.deletion.PROTECT,
                to="rdwatch.performer",
            ),
        ),
        migrations.AddIndex(
            model_name="siteobservation",
            index=django.contrib.postgres.indexes.GistIndex(
                fields=["timestamp"], name="rdwatch_sit_timesta_b3604d_gist"
            ),
        ),
        migrations.AddIndex(
            model_name="siteobservation",
            index=django.contrib.postgres.indexes.GistIndex(
                fields=["score"], name="rdwatch_sit_score_338731_gist"
            ),
        ),
        migrations.AddConstraint(
            model_name="siteobservation",
            constraint=models.UniqueConstraint(
                fields=("siteeval", "timestamp"),
                name="uniq_siteobv",
                violation_error_message="Unique constraint invalid. Add polygons to existing site observation.",
            ),
        ),
        migrations.AddIndex(
            model_name="siteevaluation",
            index=django.contrib.postgres.indexes.GistIndex(
                fields=["timestamp"], name="rdwatch_sit_timesta_4baaad_gist"
            ),
        ),
        migrations.AddIndex(
            model_name="siteevaluation",
            index=django.contrib.postgres.indexes.GistIndex(
                fields=["score"], name="rdwatch_sit_score_3ffc43_gist"
            ),
        ),
        migrations.AddConstraint(
            model_name="siteevaluation",
            constraint=models.UniqueConstraint(
                fields=("configuration", "region", "number"),
                name="unique_siteeval",
                violation_error_message="Site evaluation already exists.",
            ),
        ),
        migrations.AddIndex(
            model_name="satelliteimage",
            index=django.contrib.postgres.indexes.GistIndex(
                fields=["timestamp"], name="rdwatch_sat_timesta_f7c7c6_gist"
            ),
        ),
        migrations.AddConstraint(
            model_name="satelliteimage",
            constraint=models.UniqueConstraint(
                fields=("constellation", "spectrum", "level", "timestamp"),
                name="uniq_satimg",
                violation_error_message="Image already exists.",
            ),
        ),
        migrations.AddConstraint(
            model_name="region",
            constraint=models.UniqueConstraint(
                fields=("country", "classification", "number"),
                name="uniq_region",
                violation_error_message="Region already exists.",
            ),
        ),
    ]
