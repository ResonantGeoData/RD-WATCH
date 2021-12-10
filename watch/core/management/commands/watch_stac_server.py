from contextlib import suppress
import logging
import os
from typing import Generator, Optional

import djclick as click
import requests
from rgd.models import Collection
from rgd.models.mixins import Status
from rgd.models.utils import get_or_create_checksum_file_url
from rgd.utility import get_or_create_no_commit

from watch.core.models import STACFile
from watch.core.tasks.jobs import populate_stac_file_outline

logger = logging.getLogger(__name__)


def _iter_items(url: str, api_key: str = None) -> Generator[dict, None, None]:
    stack = [url]

    headers = {}
    if api_key:
        # Specific to SMART catalogs
        headers['x-api-key'] = api_key

    while stack:
        url = stack.pop()
        collection = requests.get(url, headers=headers).json()
        # see if there's pages
        with suppress(KeyError):
            for link in collection['links']:
                if link['rel'] == 'next':
                    stack.append(link['href'])
                    break
        # iterate through items
        for item in collection['features']:
            yield item


def _get_self_link(links):
    for link in links:
        if link['rel'] == 'self':
            return link['href']
    raise ValueError('No self link found')


@click.command()
@click.argument('host_url')  # Catalog URL
@click.option('--region', default='us-west-2')
@click.option('--collection', default=None)
@click.option('--api-key', default=None)
@click.option('--outline', default=False)
def ingest_feature_collection(
    host_url: str,
    region: str,
    collection: str,
    api_key: str = None,
    outline: Optional[bool] = False,
) -> None:

    if collection:
        collection, _ = Collection.objects.get_or_create(name=collection)
    else:
        # In case of empty strings
        collection = None

    if api_key is None:
        api_key = os.environ.get('SMART_STAC_API_KEY', None)

    for item in _iter_items(host_url, api_key=api_key):
        url = _get_self_link(item['links'])
        file, fcreated = get_or_create_checksum_file_url(url, collection=collection, defaults={})
        stacfile, screated = get_or_create_no_commit(STACFile, file=file)
        stacfile.skip_signal = True  # Do not ingest yet
        if screated:
            stacfile.status = Status.SKIPPED

        # stacfile.server_modified = 'updated'  # get from STAC Item
        stacfile.save()
        if outline:
            populate_stac_file_outline(stacfile.pk)
        logger.info(f'{"Created" if screated else "Already Present"}: {url}')
