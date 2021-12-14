import logging
from typing import Optional, Union

from rgd_client.plugin import CorePlugin, RgdPlugin

logger = logging.getLogger(__name__)


class WATCHPlugin(RgdPlugin):
    rgd: CorePlugin = CorePlugin

    def get_stac_file(self, id: Union[int, str]):
        """
        Retrieve a stac file by its ID.

        Args:
            id: The ID of the stac file
        """
        return self.session.get(f'watch/stac_file/{id}').json()

    def list_stac_file(self, file: Optional[Union[int, str]] = None):
        """List stac files."""
        params = {}
        if file:
            params['file'] = file

        return self.session.get('watch/stac_file', params=params).json()

    def post_stac_file(
        self,
        url: str,
        name: Optional[str] = None,
        collection: Optional[int] = None,
        description: Optional[str] = None,
        debug: Optional[bool] = False,
    ):
        """
        Create a Stac File from a URL ChecksumFile.

        Args:
            url: The URL to retrieve the file from
            name: The name of the file
            collection: The integer collection ID to associate this ChecksumFile with
            description: The description of the file
        """
        checksum_file = self.rgd.create_file_from_url(
            url=url,
            name=name,
            collection=collection,
            description=description,
        )

        files = self.list_stac_file(file=checksum_file['id'])
        if files['results']:
            f = files['results'][0]
            if debug:
                logger.info(f'Record already exists with ID: {f["id"]}')
            return f

        return self.session.post('watch/stac_file', json={'file': checksum_file['id']}).json()

    def reprocess_stac_file(self, id: Union[int, str]):
        """Reprocess a stac file."""
        # Submit empty patch, forcing a save
        return self.session.patch(f'watch/stac_file/{id}', data={}).json()
