import logging
from typing import Optional

import boto3
import djclick as click

from watch.core.utilities import get_or_create_stac_file, iter_matching_objects

logger = logging.getLogger(__name__)


@click.command()
@click.argument('bucket')
@click.option('--include-regex', default=r'^.*\.json')
@click.option('--prefix', default='')
@click.option('--region', default='us-west-2')
@click.option('--collection', default=None)
@click.option('--access-key-id')
@click.option('--secret-access-key')
@click.option('--outline', default=False)
def ingest_s3(
    bucket: str,
    include_regex: str,
    prefix: str,
    region: str,
    collection: str,
    access_key_id: Optional[str],
    secret_access_key: Optional[str],
    outline: Optional[bool] = False,
) -> None:
    boto3_params = {
        'region_name': region,
    }
    if access_key_id and secret_access_key:
        boto3_params['aws_access_key_id'] = access_key_id
        boto3_params['aws_secret_access_key'] = secret_access_key

    session = boto3.Session(**boto3_params)
    s3_client = session.client('s3')

    for obj in iter_matching_objects(s3_client, bucket, prefix, include_regex):
        url = f's3://{bucket}/{obj["Key"]}'
        stacfile, created = get_or_create_stac_file(
            url, collection, outline=outline, server_modified=obj['LastModified']
        )
        logger.info(f'{"Created" if created else "Already Present"}: {url}')
