import os
import logging
import tempfile
import xml.etree.ElementTree as ElementTree

from rgd.models import Collection
from rgd.utility import safe_urlopen
from rgd_imagery.management.commands import _data_helper as helper
from rgd_imagery.models import Image

from watch.core.models import GoogleCloudRecord

logger = logging.getLogger(__name__)


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
    # base_url = _format_gs_base_url(base_url)
    # Return tuples of (path, URL) : path is what is saved to model name field
    # this path should encompass the relative path of the files for the raster
    urls = [(None, base_url + '/' + name + '_' + band) for band in possible_bands]
    ancillary = [(None, base_url + '/' + name + '_' + ext) for ext in possible_anc]
    return urls, ancillary


def _make_record_dict(record, urls, ancillary):
    return helper.make_raster_dict(
        urls,
        date=str(record.sensing_time),
        name=record.product_id,
        cloud_cover=record.cloud_cover,
        ancillary_files=ancillary,
        instrumentation=record.sensor_id,
    )


def _load_landsat(record):
    urls, ancillary = _get_landsat_urls(record.base_url, record.product_id, record.sensor_id)
    return _make_record_dict(record, urls, ancillary)


def _get_sentinel_urls(base_url):
    # base_url = _format_gs_base_url(base_url)
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


def _load_sentinel(record):
    try:
        urls, ancillary = _get_sentinel_urls(record.base_url)
    except ValueError:
        logger.error(f'Failed to ingest Sentinel record: {record}')
        return None
    return _make_record_dict(record, urls, ancillary)


def load_google_cloud_record(record_pk):
    record = GoogleCloudRecord.objects.get(pk=record_pk)

    if 'gcp-public-data-landsat' in record.base_url:
        rd = _load_landsat(record)
        collection, _ = Collection.objects.get_or_create(name='GC Landsat')
    elif 'gcp-public-data-sentinel-2' in record.base_url:
        rd = _load_sentinel(record)
        collection, _ = Collection.objects.get_or_create(name='GC Sentinel')
    else:
        raise ValueError(f'Unknown base URL: {record.base_url}')
    if rd is None:
        return

    imentries = helper.load_images(rd.get('images'))
    raster = helper.load_raster(imentries, rd)
    for im in imentries:
        image = Image.objects.get(pk=im)
        image.file.collection = collection
        image.file.save(
            update_fields=[
                'collection',
            ]
        )
    for afile in raster.ancillary_files.all():
        afile.collection = collection
        afile.save(
            update_fields=[
                'collection',
            ]
        )
