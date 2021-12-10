from contextlib import suppress
import logging
import re
from typing import Generator

import requests
from rgd.models import Collection
from rgd.models.mixins import Status
from rgd.models.utils import get_or_create_checksum_file_url
from rgd.utility import get_or_create_no_commit

from watch.core.models import STACFile
from watch.core.tasks.jobs import populate_stac_file_outline

logger = logging.getLogger(__name__)


def iter_matching_objects(
    s3_client,
    bucket: str,
    prefix: str,
    include_regex: str,
) -> Generator[dict, None, None]:
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iter = paginator.paginate(Bucket=bucket, Prefix=prefix, RequestPayer='requester')
    include_pattern = re.compile(include_regex)

    for page in page_iter:
        for obj in page['Contents']:
            if include_pattern.match(obj['Key']):
                yield obj


def iter_stac_items(url: str, api_key: str = None) -> Generator[dict, None, None]:
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


def get_stac_item_self_link(links):
    for link in links:
        if link['rel'] == 'self':
            return link['href']
    raise ValueError('No self link found')


def get_or_create_stac_file(url, collection, outline=False, server_modified=None):
    if collection:
        collection, _ = Collection.objects.get_or_create(name=collection)
    else:
        # In case of empty strings
        collection = None
    file, fcreated = get_or_create_checksum_file_url(url, collection=collection, defaults={})
    stacfile, screated = get_or_create_no_commit(STACFile, file=file)
    stacfile.skip_signal = True  # Do not ingest yet
    if screated:
        stacfile.status = Status.SKIPPED
    if server_modified:
        stacfile.server_modified = server_modified
    stacfile.save()
    if outline:
        populate_stac_file_outline(stacfile.pk)
    return stacfile, screated
