import click
from aiohttp import BasicAuth

from rdwatch_cli.config import get_credentials, set_credentials


def login() -> BasicAuth:
    """Login to RD-WATCH"""

    credentials = get_credentials()
    if credentials is not None:
        return credentials

    username = click.prompt("Username", type=str)
    password = click.prompt(
        "Password",
        type=str,
        confirmation_prompt=True,
        hide_input=True,
    )
    set_credentials(username, password)
    return login()


@click.command()
def login_cmd():
    """Login to RD-WATCH"""
    login()
