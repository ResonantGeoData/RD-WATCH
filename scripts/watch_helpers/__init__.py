import concurrent.futures
from datetime import datetime, timedelta

# import multiprocessing
import os
import re
from typing import Generator, List

import boto3
import mock
from pystac_client import Client
from rgd_watch_client import create_watch_client


def iter_matching_object_urls(
    s3_client,
    bucket: str,
    prefix: str,
    include_regex: str,
) -> Generator[str, None, None]:
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iter = paginator.paginate(Bucket=bucket, Prefix=prefix, RequestPayer='requester')
    include_pattern = re.compile(include_regex)

    for page in page_iter:
        for obj in page['Contents']:
            if include_pattern.match(obj['Key']):
                yield f's3://{bucket}/{obj["Key"]}'  # TODO: modified date


def get_stac_item_self_link(links):
    for link in links:
        if link['rel'] == 'self':
            return link['href']
    raise ValueError('No self link found')


def iter_stac_item_urls(
    url: str, collections: List[str], min_date: datetime, max_date: datetime, api_key: str = None
) -> Generator[str, None, None]:
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
        results = catalog.search(collections=collections, datetime=[date, date + delta])
        for item in results.get_items():
            yield get_stac_item_self_link(item.to_dict()['links'])
        date += delta


def get_client(dry_run: bool = False):
    if True:  # dry_run: TODO
        return mock.Mock()
    return create_watch_client()


class Handler:
    def __init__(self, collection: str, dry_run: bool = False):
        self.collection = collection
        self.dry_run = dry_run

    def __call__(self, url: str):
        client = get_client(self.dry_run)
        client.watch.post_stac_file(url, self.collection)


# def handle_posts(iter_func, collection, dry_run, **kwargs):
#     pool = multiprocessing.Pool(multiprocessing.cpu_count())
#     pool.map(Handler(collection, dry_run), iter_func(**kwargs))


def handle_posts(iter_func, collection, dry_run, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        executor.map(Handler(collection, dry_run), iter_func(**kwargs))


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

    kwargs = dict(s3_client=s3_client, bucket=bucket, prefix=prefix, include_regex=include_regex)
    return handle_posts(iter_matching_object_urls, collection, dry_run, **kwargs)


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

    kwargs = dict(
        url=host_url,
        collections=[collection],
        min_date=min_date,
        max_date=max_date,
        api_key=api_key,
    )
    return handle_posts(iter_stac_item_urls, collection, dry_run, **kwargs)
