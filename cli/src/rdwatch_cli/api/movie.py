import asyncio
from datetime import datetime

import aiohttp
import click

# register pillow plugin
import pillow_avif  # type: ignore # noqa
from PIL import Image

from rdwatch_cli.api.image import image
from rdwatch_cli.exceptions import ImageNotFound, ServerError


async def try_to_fetch_image(
    client: aiohttp.ClientSession,
    bbox: tuple[float, float, float, float],
    time: datetime,
    worldview: bool = False,
):
    try:
        return await image(
            client,
            bbox,
            time,
            worldview=worldview,
        )
    except ServerError:
        click.echo(f"Skipping {time} due to server error (malformed raw image?)")
        return None


async def movie(
    client: aiohttp.ClientSession,
    bbox: tuple[float, float, float, float],
    start_time: datetime,
    end_time: datetime,
    worldview: bool = False,
) -> list[Image.Image]:

    url = (
        "/api/satellite-image/visual-timestamps"
        if worldview
        else "/api/satellite-image/timestamps"
    )

    params = {
        "start_timestamp": datetime.isoformat(start_time),
        "end_timestamp": datetime.isoformat(end_time),
        "bbox": ",".join(str(x) for x in bbox),
    }
    if not worldview:
        params["constellation"] = "S2"
        params["spectrum"] = "visual"
        params["level"] = "2A"

    resp = await client.get(url, params=params)
    timestamps = await resp.json()

    if not timestamps:
        raise ImageNotFound()
    if not resp.ok:
        raise ServerError()

    return await asyncio.gather(
        *(
            try_to_fetch_image(
                client,
                bbox,
                datetime.fromisoformat(timestamp),
                worldview=worldview,
            )
            for timestamp in timestamps
        )
    )
