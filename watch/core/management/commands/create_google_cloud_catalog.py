from datetime import datetime
import logging
import multiprocessing
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


def df_chunking(df, chunksize):
    count = 0
    while len(df):
        count += 1
        logger.info(f'Sending chunk {count}')
        # Return df chunk
        yield df.iloc[:chunksize].copy()
        # Delete data in place because it is no longer needed
        df.drop(df.index[:chunksize], inplace=True)


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


def make_records(df):
    records = [
        GoogleCloudRecord(
            catalog=GoogleCloudCatalog.objects.first(),
            base_url=_format_gs_base_url(row['BASE_URL']),
            cloud_cover=row['CLOUD_COVER'],
            product_id=row['PRODUCT_ID'],
            sensing_time=handle_date(row['SENSING_TIME']),
            sensor_id=row['SENSOR_ID'],
            bbox=bounds_to_polygon(*row[['NORTH_LAT', 'SOUTH_LAT', 'WEST_LON', 'EAST_LON']].values),
        )
        for _, row in df.iterrows()
    ]
    GoogleCloudRecord.objects.bulk_create(records, ignore_conflicts=True)
    return True


def _create_records_for_catalog(catalog, index, chunksize=1000):

    logger.info(
        f'Launching processes for index size of {len(index)} in chunks of {chunksize}. {len(index)//chunksize + 1} number of chunks.'
    )

    # HACK:
    from django import db

    db.connections.close_all()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(make_records, df_chunking(index, chunksize))

    return


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
        parser.add_argument(
            '-s',
            '--size',
            type=int,
            default=1000,
            help='Chunk size for splitting up the index during multiprocessing.',
        )

    def handle(self, *args, **options):
        start_time = datetime.now()
        count = options.get('count', None)
        size = options.get('size')

        logger.info('Loading Landsat')
        catalog, index = _get_landsat_catalog_index(count)
        _create_records_for_catalog(catalog, index, chunksize=size)

        logger.info('Loading Sentinel')
        catalog, index = _get_sentinel_catalog_index(count)
        _create_records_for_catalog(catalog, index, chunksize=size)

        self.stdout.write(
            self.style.SUCCESS('--- Completed in: {} ---'.format(datetime.now() - start_time))
        )
