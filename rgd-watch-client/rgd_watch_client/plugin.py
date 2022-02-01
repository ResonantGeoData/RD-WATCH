from typing import Optional, Union

from rgd_client.plugin import CorePlugin, RgdPlugin


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
        collection: Union[int, str],
        name: Optional[str] = None,
        description: Optional[str] = None,
        debug: Optional[bool] = False,
    ):
        """
        Create a Stac File from a URL ChecksumFile.

        Args:
            url: The URL to retrieve the file from
            collection: The integer collection ID or string name to associate
                this ChecksumFile with. To put in your default collection, pass `None`
            name: The name of the file
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
                print(f'Record already exists with ID: {f["id"]}')
            return f

        if debug:
            print('Record being created...')

        return self.session.post('watch/stac_file', json={'file': checksum_file['id']}).json()

    def reprocess_stac_file(self, id: Union[int, str]):
        """Reprocess a stac file."""
        # Submit empty patch, forcing a save
        return self.session.patch(f'watch/stac_file/{id}', data={}).json()

    def post_region(self, data: dict):
        return self.session.post('watch/region', json=data).json()

    def post_site(self, data: dict):
        return self.session.post('watch/site', json=data).json()
