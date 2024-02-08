import os
import sys
from django.urls import path
from django.core.management import execute_from_command_line
from vector_tiles.views import rgd_scoring_vector_tiles, rgd_vector_tiles

urlpatterns = [
    path(
        'api/vector-tile/<str:model_run_id>/<int:z>/<int:x>/<int:y>.pbf/',
        rgd_vector_tiles,
        name='rgd-vector-tiles',
    ),
]

if 'RDWATCH_POSTGRESQL_SCORING_URI' in os.environ:
    urlpatterns.append(
        path(
            'api/scoring/vector-tile/<str:evaluation_run_uuid>/<int:z>/<int:x>/<int:y>.pbf/',
            rgd_scoring_vector_tiles,
            name='rgd-scoring-vector-tiles',
        )
    )


if __name__ == '__main__':
    execute_from_command_line(sys.argv)
