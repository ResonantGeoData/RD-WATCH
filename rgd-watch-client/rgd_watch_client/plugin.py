from typing import Optional

from rgd_client.plugin import RgdPlugin
import validators


class WATCHPlugin(RgdPlugin):
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

        # resp = self.rgd.create_file_from_url(
        #     url=url, name=name, collection=collection, description=description
        # )

        payload = {'file': resp['id']}
        return self.session.post('watch/stac_file', json=payload).json()
