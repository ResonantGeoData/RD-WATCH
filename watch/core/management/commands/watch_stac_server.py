import logging
import os
from typing import Optional

import djclick as click

from watch.core.utilities import get_or_create_stac_file, get_stac_item_self_link, iter_stac_items

logger = logging.getLogger(__name__)


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

    if api_key is None:
        api_key = os.environ.get('SMART_STAC_API_KEY', None)

    for item in iter_stac_items(host_url, api_key=api_key):
        url = get_stac_item_self_link(item['links'])
        stacfile, created = get_or_create_stac_file(
            url,
            collection,
            outline=outline,
        )
        logger.info(f'{"Created" if created else "Already Present"}: {url}')
