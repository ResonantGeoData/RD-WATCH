from django.core.management import call_command
from django.core.management.commands.migrate import Command as MigrateCommand
from django.db import connection

CORE_RENAMED_INDEXES = [
    (
        'rdwatch_sat_status_753c74_idx',
        'core_satell_status_af6335_idx',
    ),
    (
        'rdwatch_sit_timesta_4baaad_gist',
        'core_siteev_timesta_efd110_gist',
    ),
    (
        'rdwatch_sit_score_3ffc43_gist',
        'core_siteev_score_0f673c_gist',
    ),
    (
        'rdwatch_sit_timesta_808546_gist',
        'core_siteim_timesta_411eac_gist',
    ),
    (
        'rdwatch_sit_timesta_b3604d_gist',
        'core_siteob_timesta_8249af_gist',
    ),
    (
        'rdwatch_sit_score_338731_gist',
        'core_siteob_score_ede795_gist',
    ),
]

SCORING_RENAMED_INDEXES = [
    (
        'rdwatch_sco_status_81a06c_idx',
        'scoring_sat_status_15b7ca_idx',
    ),
    (
        'rdwatch_sco_timesta_17ef97_gist',
        'scoring_sit_timesta_e3ce2d_gist',
    ),
]


class Command(MigrateCommand):
    help = 'Overridden migrate command to also handle renaming of apps.'

    def handle(self, *args, **options):
        for indexes in [CORE_RENAMED_INDEXES, SCORING_RENAMED_INDEXES]:
            for old_index_name, new_index_name in indexes:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT indexname FROM pg_indexes
                        WHERE indexname = '{old_index_name}'
                        """
                    )
                    if len(cursor.fetchall()) > 0:
                        print(f'Renaming index {old_index_name} to {new_index_name}')
                        cursor.execute(
                            f"""ALTER INDEX {old_index_name}
                            RENAME TO {new_index_name}"""
                        )

        for old_app, new_app in [
            ('rdwatch_scoring', 'scoring'),
            ('rdwatch_smartflow', 'smartflow'),
            ('rdwatch', 'core'),
        ]:
            call_command('rename_app', old_app, new_app)

        return super().handle(*args, **options)
