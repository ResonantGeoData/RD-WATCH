# flake8: noqa

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import django.contrib.postgres.indexes
from django.db import migrations, models

if TYPE_CHECKING:
    from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
    from django.db.migrations.state import StateApps


def migrate_site_evals_to_uuid(apps: StateApps, schema_editor: PostGISSchemaEditor):
    SiteEvaluationOld = apps.get_model('core', 'SiteEvaluationOld')
    SiteEvaluation = apps.get_model('core', 'SiteEvaluation')
    SiteEvaluationTracking = apps.get_model('core', 'SiteEvaluationTracking')
    SiteImage = apps.get_model('core', 'SiteImage')
    SatelliteFetching = apps.get_model('core', 'SatelliteFetching')
    SiteObservation = apps.get_model('core', 'SiteObservation')
    SiteObservationTracking = apps.get_model('core', 'SiteObservationTracking')

    for old_eval in SiteEvaluationOld.objects.iterator():
        new_eval = SiteEvaluation.objects.create(
            configuration=old_eval.configuration,
            region=old_eval.region,
            number=old_eval.number,
            timestamp=old_eval.timestamp,
            start_date=old_eval.start_date,
            end_date=old_eval.end_date,
            geom=old_eval.geom,
            label=old_eval.label,
            score=old_eval.score,
            version=old_eval.version,
            notes=old_eval.notes,
            validated=old_eval.validated,
            status=old_eval.status,
            cache_originator_file=old_eval.cache_originator_file,
            cache_timestamp=old_eval.cache_timestamp,
            cache_commit_hash=old_eval.cache_commit_hash,
        )

        SatelliteFetching.objects.filter(siteeval_old=old_eval).update(
            siteeval=new_eval
        )
        SiteImage.objects.filter(siteeval_old=old_eval).update(siteeval=new_eval)
        SiteEvaluationTracking.objects.filter(evaluation_old=old_eval).update(
            evaluation=new_eval
        )
        SiteObservation.objects.filter(siteeval_old=old_eval).update(siteeval=new_eval)
        SiteObservationTracking.objects.filter(siteeval_old=old_eval).update(
            siteeval=new_eval
        )


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0015_modelrun'),
    ]

    operations = [
        # Rename existing SiteEvaluation model and update all foreign key references
        migrations.RenameModel(old_name='SiteEvaluation', new_name='SiteEvaluationOld'),
        migrations.RenameField(
            model_name='SatelliteFetching', old_name='siteeval', new_name='siteeval_old'
        ),
        migrations.RenameField(
            model_name='SiteImage', old_name='siteeval', new_name='siteeval_old'
        ),
        migrations.RenameField(
            model_name='SiteEvaluationTracking',
            old_name='evaluation',
            new_name='evaluation_old',
        ),
        migrations.RenameField(
            model_name='SiteObservation', old_name='siteeval', new_name='siteeval_old'
        ),
        migrations.RenameField(
            model_name='SiteObservationTracking',
            old_name='siteeval',
            new_name='siteeval_old',
        ),
        # Create new models
        migrations.CreateModel(
            name='SiteEvaluation',
            fields=[
                (
                    'id',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    'number',
                    models.IntegerField(db_index=False, help_text='The site number'),
                ),
                (
                    'timestamp',
                    models.DateTimeField(
                        help_text='Time when this evaluation was finished'
                    ),
                ),
                (
                    'start_date',
                    models.DateTimeField(help_text='Start date in geoJSON', null=True),
                ),
                (
                    'end_date',
                    models.DateTimeField(help_text='end date in geoJSON', null=True),
                ),
                (
                    'geom',
                    django.contrib.gis.db.models.fields.PolygonField(
                        spatial_index=False,
                        db_index=False,
                        help_text="Polygon from this site's Site Feature",
                        srid=3857,
                    ),
                ),
                ('score', models.FloatField(help_text='Score of site footprint')),
                (
                    'version',
                    models.CharField(
                        blank=True,
                        help_text='Version of annotations',
                        max_length=255,
                        null=True,
                    ),
                ),
                ('notes', models.TextField(blank=True, null=True)),
                ('validated', models.BooleanField(blank=True, null=True)),
                (
                    'status',
                    models.CharField(
                        blank=True,
                        choices=[
                            ('PROPOSAL', 'Proposal'),
                            ('APPROVED', 'Approved'),
                            ('REJECTED', 'Rejected'),
                        ],
                        help_text='Fetching Status',
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    'cache_originator_file',
                    models.CharField(
                        blank=True,
                        help_text='Name of source file for proposals',
                        max_length=2048,
                        null=True,
                    ),
                ),
                (
                    'cache_timestamp',
                    models.DateTimeField(
                        help_text='Cache timestamp for proposals', null=True
                    ),
                ),
                (
                    'cache_commit_hash',
                    models.CharField(
                        blank=True,
                        help_text='Hash of the file for proposals',
                        max_length=2048,
                        null=True,
                    ),
                ),
                (
                    'configuration',
                    models.ForeignKey(
                        db_index=False,
                        help_text='The hyper parameters used this site evaluation.',
                        on_delete=django.db.models.deletion.PROTECT,
                        to='core.modelrun',
                    ),
                ),
                (
                    'label',
                    models.ForeignKey(
                        db_index=False,
                        help_text='Site feature classification label',
                        on_delete=django.db.models.deletion.PROTECT,
                        to='core.observationlabel',
                    ),
                ),
                (
                    'region',
                    models.ForeignKey(
                        db_index=False,
                        help_text='The region this site belongs to',
                        on_delete=django.db.models.deletion.PROTECT,
                        to='core.region',
                    ),
                ),
            ],
            options={
                'default_related_name': 'evaluations',
            },
        ),
        # Create new FK columns pointing to new SiteEvaluation model, but make them
        # nullable for now. We also don't add indexes to them yet, as Django doesn't
        # seem to like that until we delete the old ones.
        migrations.AddField(
            model_name='satellitefetching',
            name='siteeval',
            field=models.OneToOneField(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='satellite_fetching',
                to='core.siteevaluation',
            ),
        ),
        migrations.AddField(
            model_name='siteevaluationtracking',
            name='evaluation',
            field=models.ForeignKey(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.siteevaluation',
            ),
        ),
        migrations.AddField(
            model_name='siteimage',
            name='siteeval',
            field=models.ForeignKey(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.siteevaluation',
            ),
        ),
        migrations.AddField(
            model_name='siteobservation',
            name='siteeval',
            field=models.ForeignKey(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.siteevaluation',
            ),
        ),
        migrations.AddField(
            model_name='siteobservationtracking',
            name='siteeval',
            field=models.ForeignKey(
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.siteevaluation',
            ),
        ),
        # Update existing references to point to instances of new model
        migrations.RunPython(migrate_site_evals_to_uuid),
        # Remove temporary fields now that data migration is complete
        migrations.RemoveField(
            model_name='siteevaluationold',
            name='configuration',
        ),
        migrations.RemoveField(
            model_name='siteevaluationold',
            name='label',
        ),
        migrations.RemoveField(
            model_name='siteevaluationold',
            name='region',
        ),
        migrations.RemoveField(
            model_name='satellitefetching',
            name='siteeval_old',
        ),
        migrations.RemoveField(
            model_name='siteevaluationtracking',
            name='evaluation_old',
        ),
        migrations.RemoveField(
            model_name='siteimage',
            name='siteeval_old',
        ),
        migrations.RemoveField(
            model_name='siteobservation',
            name='siteeval_old',
        ),
        migrations.RemoveField(
            model_name='siteobservationtracking',
            name='siteeval_old',
        ),
        # Delete the old model
        migrations.DeleteModel(
            name='SiteEvaluationOld',
        ),
        # Now that they are populated, make FK's non-nullable and add indexes for them
        migrations.AlterField(
            model_name='satellitefetching',
            name='siteeval',
            field=models.OneToOneField(
                db_index=True,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='satellite_fetching',
                to='core.siteevaluation',
            ),
        ),
        migrations.AlterField(
            model_name='siteevaluation',
            name='configuration',
            field=models.ForeignKey(
                db_index=True,
                null=False,
                help_text='The hyper parameters used this site evaluation.',
                on_delete=django.db.models.deletion.PROTECT,
                to='core.modelrun',
            ),
        ),
        migrations.AlterField(
            model_name='siteevaluation',
            name='geom',
            field=django.contrib.gis.db.models.fields.PolygonField(
                spatial_index=True,
                help_text="Polygon from this site's Site Feature",
                srid=3857,
            ),
        ),
        migrations.AlterField(
            model_name='siteevaluation',
            name='label',
            field=models.ForeignKey(
                db_index=True,
                null=False,
                help_text='Site feature classification label',
                on_delete=django.db.models.deletion.PROTECT,
                to='core.observationlabel',
            ),
        ),
        migrations.AlterField(
            model_name='siteevaluation',
            name='number',
            field=models.IntegerField(db_index=True, help_text='The site number'),
        ),
        migrations.AlterField(
            model_name='siteevaluation',
            name='region',
            field=models.ForeignKey(
                db_index=True,
                null=False,
                help_text='The region this site belongs to',
                on_delete=django.db.models.deletion.PROTECT,
                to='core.region',
            ),
        ),
        migrations.AlterField(
            model_name='siteevaluationtracking',
            name='evaluation',
            field=models.ForeignKey(
                db_index=True,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.siteevaluation',
            ),
        ),
        migrations.AlterField(
            model_name='siteimage',
            name='siteeval',
            field=models.ForeignKey(
                db_index=True,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.siteevaluation',
            ),
        ),
        migrations.AlterField(
            model_name='siteobservation',
            name='siteeval',
            field=models.ForeignKey(
                db_index=True,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.siteevaluation',
            ),
        ),
        migrations.AlterField(
            model_name='siteobservationtracking',
            name='siteeval',
            field=models.ForeignKey(
                db_index=True,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.siteevaluation',
            ),
        ),
        # Add indexes back
        migrations.AddIndex(
            model_name='siteevaluation',
            index=django.contrib.postgres.indexes.GistIndex(
                fields=['timestamp'], name='rdwatch_sit_timesta_4baaad_gist'
            ),
        ),
        migrations.AddIndex(
            model_name='siteevaluation',
            index=django.contrib.postgres.indexes.GistIndex(
                fields=['score'], name='rdwatch_sit_score_3ffc43_gist'
            ),
        ),
    ]
