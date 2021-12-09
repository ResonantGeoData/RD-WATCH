import logging
from typing import Generator, Optional

import djclick as click
from rgd.models import Collection
from rgd.models.mixins import Status
from rgd.models.utils import get_or_create_checksum_file_url
from rgd.utility import get_or_create_no_commit

from watch.core.models import STACFile
from watch.core.tasks.jobs import populate_stac_file_outline

logger = logging.getLogger(__name__)


def iterator():
    return ...


@click.command()
@click.argument('host_url')  # Catalog URL
@click.option('--region', default='us-west-2')
@click.option('--collection', default=None)
@click.option('--outline', default=False)
def ingest_s3(
    host_url: str,
    region: str,
    collection: str,
    outline: Optional[bool] = False,
) -> None:

    if collection:
        collection, _ = Collection.objects.get_or_create(name=collection)
    else:
        # In case of empty strings
        collection = None

    for item in iterator(host_url):
        url = item['links']['self']
        file, fcreated = get_or_create_checksum_file_url(url, collection=collection, defaults={})
        stacfile, screated = get_or_create_no_commit(STACFile, file=file)
        stacfile.skip_signal = True  # Do not ingest yet
        if screated:
            stacfile.status = Status.SKIPPED

        # stacfile.server_modified = "updated"  # get from STAC Item
        stacfile.save()
        if outline:
            populate_stac_file_outline(stacfile.pk)
        logger.info(f'{"Created" if screated else "Already Present"}: {url}')
