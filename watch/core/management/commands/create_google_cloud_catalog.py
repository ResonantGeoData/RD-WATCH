from datetime import datetime
import logging
import os

import dateutil.parser
from django.contrib.gis.geos import Polygon
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
import pandas as pd
import pooch
from pooch import Decompress
from rgd.models import ChecksumFile

from watch.core.models import GoogleCloudCatalog, GoogleCloudRecord

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)


def _format_gs_base_url(base_url):
    return 'http://storage.googleapis.com/' + base_url.replace('gs://', '')


def _fetch_landsat_index_table(count=None):
    file_path = pooch.retrieve(
        url=_format_gs_base_url('gs://gcp-public-data-landsat/index.csv.gz'),
        known_hash=None,
        processor=Decompress(),
        path=DATA_DIR,
    )
    index = pd.read_csv(file_path, nrows=count)
    index = index[index['SENSOR_ID'].isin(['OLI_TIRS', 'ETM'])]
    index = index[pd.to_datetime(index['SENSING_TIME']).dt.year >= 2007]
    return index


def _fetch_sentinel_index_table(count=None):
    file_path = pooch.retrieve(
        url=_format_gs_base_url('gs://gcp-public-data-sentinel-2/index.csv.gz'),
        known_hash=None,
        processor=Decompress(),
        path=DATA_DIR,
    )
    df = pd.read_csv(file_path, nrows=count)
    # Handle issue where tiles for a given date were processed multiple times
    #   to avoid ingesting duplicate data.
    clean = (
        df.sort_values('PRODUCT_ID')
        .drop_duplicates(['MGRS_TILE', 'SENSING_TIME'], keep='first')
        .sort_index()
    )
    # Normalize
    clean['SENSOR_ID'] = clean['PRODUCT_ID'].str.split('_').str[0]
    return clean


def _get_landsat_catalog_index(count=None):
    landsat_index, _ = ChecksumFile.objects.get_or_create(
        url='http://storage.googleapis.com/gcp-public-data-landsat/index.csv.gz',
        type=2,
        defaults=dict(name='Google Cloud Landsat Index'),
    )
    catalog, _ = GoogleCloudCatalog.objects.get_or_create(index=landsat_index)
    index = _fetch_landsat_index_table(count=count)
    return catalog, index


def _get_sentinel_catalog_index(count=None):
    sentinel_index, _ = ChecksumFile.objects.get_or_create(
        url='http://storage.googleapis.com/gcp-public-data-sentinel-2/index.csv.gz',
        type=2,
        defaults=dict(name='Google Cloud Sentinel 2 Index'),
    )
    catalog, _ = GoogleCloudCatalog.objects.get_or_create(index=sentinel_index)
    index = _fetch_sentinel_index_table(count=count)
    return catalog, index


def _create_records_for_catalog(catalog, index):
    def bounds_to_polygon(north, south, west, east):
        return Polygon(
            (
                (west, north),
                (east, north),
                (east, south),
                (west, south),
                (west, north),
            ),
            srid=4326,
        )

    def handle_date(date):
        adt = dateutil.parser.isoparser().isoparse(date)
        try:
            adt = make_aware(adt)
        except ValueError:
            pass
        return adt

    logger.info('Creating records without comitting...')

    records = [
        GoogleCloudRecord(
            catalog=catalog,
            base_url=_format_gs_base_url(row['BASE_URL']),
            cloud_cover=row['CLOUD_COVER'],
            product_id=row['PRODUCT_ID'],
            sensing_time=handle_date(row['SENSING_TIME']),
            sensor_id=row['SENSOR_ID'],
            bbox=bounds_to_polygon(*row[['NORTH_LAT', 'SOUTH_LAT', 'WEST_LON', 'EAST_LON']].values),
        )
        for _, row in index.iterrows()
    ]

    logger.info('Running bulk create...')

    return GoogleCloudRecord.objects.bulk_create(records, ignore_conflicts=True)


class Command(BaseCommand):
    help = 'Populate database with demo landsat data from S3.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--count',
            type=int,
            help='Indicates the number scenes to fetch. The actual number of '
            'rasters ingested will be less than this as this is the number '
            'that are taken off the top of the catalog and '
            'duplicates/irrelevant data are dropped.',
            default=None,
        )

    def handle(self, *args, **options):
        start_time = datetime.now()
        count = options.get('count', None)

        catalog, index = _get_landsat_catalog_index(count)
        _create_records_for_catalog(catalog, index)

        catalog, index = _get_sentinel_catalog_index(count)
        _create_records_for_catalog(catalog, index)

        self.stdout.write(
            self.style.SUCCESS('--- Completed in: {} ---'.format(datetime.now() - start_time))
        )
