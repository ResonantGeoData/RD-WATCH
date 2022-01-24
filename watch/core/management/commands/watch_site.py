from glob import glob
import json
import logging

import djclick as click

from watch.core.serializers import SiteSerializer

logger = logging.getLogger(__name__)


@click.command()
@click.argument('directory')
def ingest_s3(
    directory: str,
) -> None:
    """Must ingest Regions first!!"""
    # Glob all .geojson files under the directory - recursively
    files = glob(f'{directory}/**/*.geojson', recursive=True)

    for path in files:
        print(path)
        with open(path, 'r') as f:
            feature_collection = json.load(f)

        SiteSerializer().create(feature_collection)
