from contextlib import suppress
import logging
import os
import re
from typing import Generator

import boto3
import requests
from rgd_client import create_rgd_client

# API_URL = 'https://watch.resonantgeodata.com/api'
API_URL = 'http://localhost:8000/api'

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


def post_stac_items_from_s3_iter(
    bucket: str,
    prefix: str,
    collection: str,
    region: str = 'us-west-2',
    include_regex: str = r'^.*\.json',
    dry_run: bool = True,  # TODO
):
    boto3_params = {
        'region_name': region,
    }
    session = boto3.Session(**boto3_params)
    s3_client = session.client('s3')

    if not dry_run:
        client = create_rgd_client(api_url=API_URL)
    for obj in iter_matching_objects(s3_client, bucket, prefix, include_regex):
        url = f's3://{bucket}/{obj["Key"]}'
        if not dry_run:
            client.watch.post_stac_file(url=url, collection=collection)
        else:
            logger.info(url)


def post_stac_items_from_server(
    host_url: str,
    collection: str,
    api_key: str = None,
    dry_run: bool = True,  # TODO
):
    if api_key is None:
        api_key = os.environ.get('SMART_STAC_API_KEY', None)

    if not dry_run:
        client = create_rgd_client(api_url=API_URL)
    for item in iter_stac_items(host_url, api_key=api_key):
        url = get_stac_item_self_link(item['links'])
        if not dry_run:
            client.watch.post_stac_file(url=url, collection=collection)
        else:
            logger.info(url)
