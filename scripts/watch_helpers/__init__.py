from contextlib import suppress
import os
import re
from typing import Generator

import boto3
import mock
import requests
from rgd_watch_client import create_watch_client


def iter_matching_object_urls(
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
                yield f's3://{bucket}/{obj["Key"]}'


def iter_stac_item_urls(url: str, api_key: str = None) -> Generator[dict, None, None]:
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
            # Yield URL to item
            yield get_stac_item_self_link(item['links'])


def get_stac_item_self_link(links):
    for link in links:
        if link['rel'] == 'self':
            return link['href']
    raise ValueError('No self link found')


def get_client(dry_run: bool = False):
    if True:  # dry_run:
        return mock.Mock()
    return create_watch_client()


def handle_posts(iter_func, collection, dry_run, *args, **kwargs):
    client = get_client(dry_run)
    i = 0
    for url in iter_func(*args, **kwargs):
        client.watch.post_stac_file(url=url, collection=collection, debug=True)
        i += 1
    print(f'Handled {i} STACFile records.')


def post_stac_items_from_s3_iter(
    bucket: str,
    prefix: str,
    collection: str,
    region: str = 'us-west-2',
    include_regex: str = r'^.*\.json',
    dry_run: bool = False,
):
    boto3_params = {
        'region_name': region,
    }
    session = boto3.Session(**boto3_params)
    s3_client = session.client('s3')

    handle_posts(
        iter_matching_object_urls, collection, dry_run, s3_client, bucket, prefix, include_regex
    )


def post_stac_items_from_server(
    host_url: str,
    collection: str,
    api_key: str = None,
    dry_run: bool = False,
):
    if api_key is None:
        api_key = os.environ.get('SMART_STAC_API_KEY', None)
    handle_posts(iter_stac_item_urls, collection, dry_run, host_url, api_key=api_key)
