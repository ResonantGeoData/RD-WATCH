import aiohttp

from rdwatch_cli.login import login


def get_http_client() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        auth=login(),
        base_url="https://resonantgeodata.dev",
        timeout=aiohttp.ClientTimeout(
            sock_read=120,
            connect=None,
            sock_connect=None,
            total=None,
        ),
        connector=aiohttp.TCPConnector(limit=30),
    )
