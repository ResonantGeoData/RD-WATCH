from typing import Optional, Union

from rgd_client.plugin import RgdPlugin
import validators


class WATCHPlugin(RgdPlugin):
    def get_stac_file(self, id: Union[int, str]):
        """
        Retrieve a stac file by its ID.

        Args:
            id: The ID of the stac file
        """
        return self.session.get(f'watch/stac_file/{id}').json()

    def list_stac_file(self):
        """List stac files."""
        return self.session.get('watch/stac_file').json()

    def post_stac_file(
        self,
        url: str,
        name: Optional[str] = None,
        collection: Optional[int] = None,
        description: Optional[str] = None,
    ):
        """
        Create a ChecksumFile from a URL.

        Args:
            url: The URL to retrieve the file from
            name: The name of the file
            collection: The integer collection ID to associate this ChecksumFile with
            description: The description of the file
        """
        # Verify that url is valid in shape, will raise error on failure
        validators.url(url)

        # Construct payload, leaving out empty arguments
        payload = {'url': url, 'type': 2}
        if name is not None:
            payload['name'] = name
        if collection is not None:
            payload['collection'] = collection
        if description is not None:
            payload['description'] = description

        r = self.session.post('rgd/checksum_file', json=payload)

        r.raise_for_status()
        resp = r.json()

        payload = {'file': resp['id']}
        return self.session.post('watch/stac_file', json=payload).json()

    def reprocess_stac_file(self, id: Union[int, str]):
        """Reprocess a stac file."""
        # Submit empty patch, forcing a save
        return self.session.patch(f'watch/stac_file/{id}', data={}).json()
