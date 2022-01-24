from glob import glob
import json
import logging

import dateutil.parser
from django.contrib.gis.geos import GEOSGeometry
import djclick as click
from shapely.geometry import shape
from shapely.wkb import dumps

from watch.core.models import Feature, Region

logger = logging.getLogger(__name__)


def populate(record, feature):
    record.properties = feature['properties']
    geom = shape(feature['geometry'])
    record.footprint = GEOSGeometry(memoryview(dumps(geom)))
    record.outline = GEOSGeometry(memoryview(dumps(geom.envelope)))
    record.save()


def add_dates(record, feature):
    date = feature['properties']['start_date']
    if date:
        record.start_date = dateutil.parser.parse(date)
    date = feature['properties']['end_date']
    if date:
        record.end_date = dateutil.parser.parse(date)


@click.command()
@click.argument('directory')
def ingest_s3(
    directory: str,
) -> None:
    # Glob all .geojson files under the directory - recursively
    files = glob(f'{directory}/**/*.geojson', recursive=True)

    for path in files:
        print(path)
        with open(path, 'r') as f:
            feature_collection = json.load(f)

        # find index of region
        region_index = None
        for i, feature in enumerate(feature_collection['features']):
            if feature['properties']['type'] == 'region':
                region_index = i
                break
        if region_index is None:
            raise ValueError('No `region` type in FeatureCollection.')
        feature = feature_collection['features'].pop(region_index)

        region = Region()
        populate(region, feature)

        for feature in feature_collection['features']:
            if feature['properties']['type'] == 'region':
                raise ValueError('Multiple `region` types in FeatureCollection.')
            else:
                record = Feature()
                record.parent_region = region
                add_dates(record, feature)
            populate(record, feature)
