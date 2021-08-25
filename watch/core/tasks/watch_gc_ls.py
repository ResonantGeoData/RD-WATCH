from datetime import datetime
import json
import logging
import billiard as multiprocessing
import os
import tempfile
import xml.etree.ElementTree as ElementTree

import geopandas as gpd
import pandas as pd
import pooch
from pooch import Decompress
from rgd.models import Collection
from rgd.utility import safe_urlopen
from rgd_imagery.management.commands import _data_helper as helper
from rgd_imagery.models import Image
from shapely.geometry import shape

from watch.core.models import Region

logger = logging.getLogger(__name__)

SUCCESS_MSG = 'Finished loading all {} data.'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def _format_gs_base_url(base_url):
    return 'http://storage.googleapis.com/' + base_url.replace('gs://', '')


def _fetch_landsat_index_table():
    file_path = pooch.retrieve(
        url=_format_gs_base_url('gs://gcp-public-data-landsat/index.csv.gz'),
        known_hash=None,
        processor=Decompress(),
        path=DATA_DIR,
    )
    return pd.read_csv(file_path)


def _fetch_sentinel_index_table():
    file_path = pooch.retrieve(
        url=_format_gs_base_url('gs://gcp-public-data-sentinel-2/index.csv.gz'),
        known_hash=None,
        processor=Decompress(),
        path=DATA_DIR,
    )
    df = pd.read_csv(file_path)
    # Handle issue where tiles for a given date were processed multiple times
    #   to avoid ingesting duplicate data.
    clean = df.sort_values('PRODUCT_ID').drop_duplicates(
        ['MGRS_TILE', 'SENSING_TIME'], keep='first'
    )
    return clean.sort_index()


def _get_landsat_index_from_geojson(index, geojson, start_date, end_date):
    logger.info(f'Dates: {start_date} through {end_date}')
    roi = shape(geojson)
    landsat_geom = gpd.read_file(os.path.join(DATA_DIR, 'WRS2_descending.shp'))
    found = landsat_geom[landsat_geom.geometry.intersects(roi)][['PATH', 'ROW']]
    found['WRS_PATH'] = found['PATH']
    found['WRS_ROW'] = found['ROW']
    found = found.drop(['PATH', 'ROW'], axis=1)
    subset = pd.merge(index, found, how='inner', on=['WRS_PATH', 'WRS_ROW'])
    subset = subset[subset['SENSOR_ID'].isin(['OLI_TIRS', 'ETM'])]
    # Handle date range
    subset['DATE_ACQUIRED'] = pd.to_datetime(subset['DATE_ACQUIRED'])
    subset = subset[subset['DATE_ACQUIRED'] >= start_date]
    subset = subset[subset['DATE_ACQUIRED'] <= end_date]
    logger.info(f'Found: {len(subset)}')
    return subset


def _get_sentinel_index_from_geojson(index, geojson, start_date, end_date):
    roi = shape(geojson)
    sentinel_geom = gpd.read_file(os.path.join(DATA_DIR, 'sentinel_2_index_shapefile.shp'))
    found = sentinel_geom[sentinel_geom.geometry.intersects(roi)]
    found['MGRS_TILE'] = found['Name']
    found = found.drop(['Name'], axis=1)
    found.head()
    subset = pd.merge(index, found.drop(['geometry'], axis=1), how='inner', on=['MGRS_TILE'])
    # Handle date range
    subset['SENSING_TIME'] = pd.to_datetime(subset['SENSING_TIME'])
    subset = subset[subset['SENSING_TIME'] >= start_date]
    subset = subset[subset['SENSING_TIME'] <= end_date]
    return subset


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


def _get_landsat_index_from_features(index, features):
    return pd.concat(
        [
            _get_landsat_index_from_geojson(
                index, json.loads(feature.footprint.json), datetime.combine(feature.start_date, datetime.min.time()), datetime.combine(feature.end_date, datetime.max.time())
            )
            for feature in features
        ]
    )


def _get_sentinel_index_from_features(index, features):
    return pd.concat(
        [
            _get_sentinel_index_from_geojson(
                index, json.loads(feature.footprint.json), feature.start_date, feature.end_date
            )
            for feature in features
        ]
    )


class GCLoader:
    def __init__(self, satellite, features, footprint=False):
        if satellite not in ['landsat', 'sentinel']:
            raise ValueError(f'Unknown satellite {satellite}.')
        self.satellite = satellite

        if self.satellite == 'landsat':
            index = _fetch_landsat_index_table()
            self.index = _get_landsat_index_from_features(index, features)
            self.collection, _ = Collection.objects.get_or_create(name='Landsat')
        elif self.satellite == 'sentinel':
            index = _fetch_sentinel_index_table()
            self.index = _get_sentinel_index_from_features(index, features)
            self.collection, _ = Collection.objects.get_or_create(name='Sentinel')

        self.footprint = footprint

    def _load_raster(self, index):
        row = self.index.iloc[index]
        if self.satellite == 'landsat':
            rd = _load_landsat(row)
        elif self.satellite == 'sentinel':
            rd = _load_sentinel(row)
        else:
            raise ValueError(f'Unknown satellite: {self.satellite}')
        if rd is None:
            return
        imentries = helper.load_images(rd.get('images'))
        raster = helper.load_raster(imentries, rd, footprint=self.footprint)
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

    def load_rasters(self, count=None):
        if not count:
            count = len(self.index)
        logger.info(f'Processing {count} rasters...')
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        pool.map(self._load_raster, range(count))


def load_region_landsat(region_pk):
    region = Region.objects.get(pk=region_pk)
    loader = GCLoader('landsat', region.feature_set.all())
    loader.load_rasters()
