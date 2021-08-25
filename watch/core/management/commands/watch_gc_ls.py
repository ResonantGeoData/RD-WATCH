from datetime import datetime
import logging
import os
import tempfile
import xml.etree.ElementTree as ElementTree

from django.core.management.base import BaseCommand
import pandas as pd
import pooch
from pooch import Decompress
from rgd.models import Collection
from rgd.utility import safe_urlopen
from rgd_imagery.management.commands import _data_helper as helper
from rgd_imagery.models import Image

logger = logging.getLogger(__name__)

SUCCESS_MSG = 'Raster records created. Please monitor celery worker for ingestion status.'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)


def _format_gs_base_url(base_url):
    return 'http://storage.googleapis.com/' + base_url.replace('gs://', '')


def _fetch_landsat_index_table(count=None):
    file_path = pooch.retrieve(
        url=_format_gs_base_url('gs://gcp-public-data-landsat/index.csv.gz'),
        known_hash=None,  # 7ccce260df5f7ad77a24f8f24acd944bee210ee5c44b3dcdd37e14f98a6876af
        processor=Decompress(),
        path=DATA_DIR,
    )
    index = pd.read_csv(file_path, nrows=count)
    index = index[index['SENSOR_ID'].isin(['OLI_TIRS', 'ETM'])]
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
    clean = df.sort_values('PRODUCT_ID').drop_duplicates(
        ['MGRS_TILE', 'SENSING_TIME'], keep='first'
    )
    return clean.sort_index()


def _get_landsat_urls(base_url, name, sensor):
    if sensor == 'OLI_TIRS':  # Landsat 8
        possible_bands = [
            'B1.TIF',
            'B2.TIF',
            'B3.TIF',
            'B4.TIF',
            'B5.TIF',
            'B6.TIF',
            'B7.TIF',
            'B8.TIF',
            'B9.TIF',
            'B10.TIF',
            'B11.TIF',
            'BQA.TIF',
        ]
        possible_anc = [
            'ANG.txt',
            'MTL.txt',
        ]
    elif sensor == 'ETM':  # Landsat 7
        possible_bands = [
            'B1.TIF',
            'B2.TIF',
            'B3.TIF',
            'B4.TIF',
            'B5.TIF',
            # 'B6.TIF',
            'B6_VCID_1.TIF',
            'B6_VCID_2.TIF',
            'B7.TIF',
            'B8.TIF',
            # 'B9.TIF',
            'BQA.TIF',
        ]
        possible_anc = [
            'ANG.txt',
            'MTL.txt',
        ]
    else:
        raise ValueError(f'Unknown sensor: {sensor}')
    base_url = _format_gs_base_url(base_url)
    # Return tuples of (path, URL) : path is what is saved to model name field
    # this path should encompass the relative path of the files for the raster
    urls = [(None, base_url + '/' + name + '_' + band) for band in possible_bands]
    ancillary = [(None, base_url + '/' + name + '_' + ext) for ext in possible_anc]
    return urls, ancillary


def _load_landsat(row):
    urls, ancillary = _get_landsat_urls(row['BASE_URL'], row['PRODUCT_ID'], row['SENSOR_ID'])
    rd = helper.make_raster_dict(
        urls,
        date=row['SENSING_TIME'],
        name=row['PRODUCT_ID'],
        cloud_cover=row['CLOUD_COVER'],
        ancillary_files=ancillary,
        instrumentation=row['SENSOR_ID'],
    )
    return rd


def _get_sentinel_urls(base_url):
    base_url = _format_gs_base_url(base_url)
    manifest_url = base_url + '/manifest.safe'
    with safe_urlopen(manifest_url) as remote, tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, 'manifest.safe')
        with open(manifest_path, 'wb') as f:
            f.write(remote.read())
        # Now check to see if `MTD_TL.xml` is in the manifest ONCE - if more or less, skip it.
        # Ask Matthew Bernstein for insight
        with open(manifest_path, 'r') as f:
            if f.read().count('MTD_TL.xml') != 1:
                raise ValueError('This entry is bad.')
        tree = ElementTree.parse(manifest_path)

    urls = []
    ancillary = []
    # Return tuples of (path, URL) : path is what is saved to model name field
    # this path should encompass the relative path of the files for the raster
    root = tree.getroot()
    meta = root.find('dataObjectSection')
    for c in meta:
        f = c.find('byteStream').find('fileLocation')
        href = f.attrib['href'][2::]  # to remove `./`
        di = href.split('/')[0]
        if di in [
            'GRANULE',
        ]:
            url = base_url + '/' + href
            if url[-4:] == '.jp2':
                urls.append((href, url))
            else:
                ancillary.append((href, url))

    return urls, ancillary


def _load_sentinel(row):
    try:
        urls, ancillary = _get_sentinel_urls(row['BASE_URL'])
    except ValueError:
        return None
    rd = helper.make_raster_dict(
        urls,
        date=row['SENSING_TIME'],
        name=row['PRODUCT_ID'],
        cloud_cover=row['CLOUD_COVER'],
        ancillary_files=ancillary,
        instrumentation=row['PRODUCT_ID'].split('_')[0],
    )
    return rd


class GCLoader:
    def __init__(self, satellite):
        if satellite not in ['landsat', 'sentinel']:
            raise ValueError(f'Unknown satellite {satellite}.')
        self.satellite = satellite

        if self.satellite == 'landsat':
            self.collection, _ = Collection.objects.get_or_create(name='GC Landsat')
        elif self.satellite == 'sentinel':
            self.collection, _ = Collection.objects.get_or_create(name='GC Sentinel')

    def _load_raster(self, idx, row):
        if self.satellite == 'landsat':
            rd = _load_landsat(row)
        elif self.satellite == 'sentinel':
            rd = _load_sentinel(row)
        else:
            raise ValueError(f'Unknown satellite: {self.satellite}')
        if rd is None:
            return
        imentries = helper.load_images(rd.get('images'))
        raster = helper.load_raster(imentries, rd)
        for im in imentries:
            image = Image.objects.get(pk=im)
            image.file.collection = self.collection
            image.file.save(
                update_fields=[
                    'collection',
                ]
            )
        for afile in raster.ancillary_files.all():
            afile.collection = self.collection
            afile.save(
                update_fields=[
                    'collection',
                ]
            )

    def load_rasters(self, index):
        iterable = index.iterrows()
        logger.info(f'Processing {len(index)} rasters...')
        for i, (a, b) in enumerate(iterable):
            logger.info(f'Creating records for raster {i+1}/{len(index)}')
            self._load_raster(a, b)


class Command(BaseCommand):
    help = 'Populate database with demo landsat data from S3.'

    def add_arguments(self, parser):
        parser.add_argument('satellite', type=str, help='landsat or sentinel')
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
        count = options.get('count', None)
        satellite = options.get('satellite')

        start_time = datetime.now()

        loader = GCLoader(satellite)

        if satellite == 'landsat':
            index = _fetch_landsat_index_table(count)
        elif satellite == 'sentinel':
            index = _fetch_sentinel_index_table(count)
        loader.load_rasters(index)

        self.stdout.write(
            self.style.SUCCESS('--- Completed in: {} ---'.format(datetime.now() - start_time))
        )
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
