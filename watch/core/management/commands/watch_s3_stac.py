import logging
import re
from typing import Generator, Optional

import boto3
import djclick as click
from rgd.models import Collection
from rgd.models.mixins import Status
from rgd.models.utils import get_or_create_checksum_file_url
from rgd.utility import get_or_create_no_commit

from watch.core.models import STACFile

logger = logging.getLogger(__name__)


def _iter_matching_objects(
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


@click.command()
@click.argument('bucket')
@click.option('--include-regex', default=r'^.*\.json')
@click.option('--prefix', default='')
@click.option('--region', default='us-west-2')
@click.option('--collection', default=None)
@click.option('--access-key-id')
@click.option('--secret-access-key')
def ingest_s3(
    bucket: str,
    include_regex: str,
    prefix: str,
    region: str,
    collection: str,
    access_key_id: Optional[str],
    secret_access_key: Optional[str],
) -> None:
    boto3_params = {
        'region_name': region,
    }
    if access_key_id and secret_access_key:
        boto3_params['aws_access_key_id'] = access_key_id
        boto3_params['aws_secret_access_key'] = secret_access_key

    session = boto3.Session(**boto3_params)
    s3_client = session.client('s3')

    if collection:
        collection, _ = Collection.objects.get_or_create(name=collection)
    else:
        # In case of empty strings
        collection = None

    for obj in _iter_matching_objects(s3_client, bucket, prefix, include_regex):
        url = f's3://{bucket}/{obj["Key"]}'
        file, fcreated = get_or_create_checksum_file_url(url, collection=collection, defaults={})
        stacfile, screated = get_or_create_no_commit(STACFile, checksumfile=file)
        stacfile.skip_signal = True  # Do not ingest yet
        if screated:
            stacfile.status = Status.SKIPPED
        stacfile.server_modified = obj['LastModified']
        stacfile.save()
        logger.info(f'{"Created" if screated else "Already Present"}: {url}')
