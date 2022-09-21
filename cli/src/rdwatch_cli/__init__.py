import click

from rdwatch_cli.image import image_cmd
from rdwatch_cli.login import login_cmd
from rdwatch_cli.movie import movie_cmd


@click.group()
def cli():
    ...


cli.add_command(login_cmd, name="login")
cli.add_command(image_cmd, name="image")
cli.add_command(movie_cmd, name="movie")
