from datetime import datetime, timedelta
import os
import re
from typing import Generator, List

import boto3
import mock
from pystac_client import Client
from rgd_watch_client import create_watch_client


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


def iter_stac_items(
    url: str, collections: List[str], min_date: datetime, max_date: datetime, api_key: str = None
) -> Generator[dict, None, None]:
    if max_date <= min_date:
        raise ValueError('End date must be after start date.')

    headers = {}
    if api_key:
        # Specific to SMART catalogs
        headers['x-api-key'] = api_key

    date = min_date
    catalog = Client.open(url, headers=headers)
    delta = timedelta(days=1)
    while date <= max_date:
        print(date)  # DEBUG
        results = catalog.search(collections=['landsat-c2l1'], datetime=[date, date + delta])
        for item in results.get_items():
            yield item.to_dict()
        date += delta


def get_stac_item_self_link(links):
    for link in links:
        if link['rel'] == 'self':
            return link['href']
    raise ValueError('No self link found')


def get_client(dry_run: bool = False):
    if True:  # dry_run: TODO
        return mock.Mock()
    return create_watch_client()


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

    client = get_client(dry_run)
    i = 0
    for obj in iter_matching_objects(s3_client, bucket, prefix, include_regex):
        url = f's3://{bucket}/{obj["Key"]}'
        client.watch.post_stac_file(url=url, collection=collection, debug=True)
        i += 1
    print(f'Handled {i} STACFile records.')


def post_stac_items_from_server(
    host_url: str,
    collection: str,
    min_date: datetime,
    max_date: datetime,
    api_key: str = None,
    dry_run: bool = False,
):
    if api_key is None:
        api_key = os.environ.get('SMART_STAC_API_KEY', None)

    client = get_client(dry_run)
    i = 0
    for item in iter_stac_items(
        host_url, collections=[collection], min_date=min_date, max_date=max_date, api_key=api_key
    ):
        url = get_stac_item_self_link(item['links'])
        print(url)  # DEBUG
        client.watch.post_stac_file(url=url, collection=collection, debug=True)
        i += 1
    print(f'Handled {i} STACFile records.')
