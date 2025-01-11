import sys

import click

from ..config import load_config
from ..environment import Environment
from ..environment import pass_env
from .cli import cli


def ensure_token(env: Environment) -> str:
    config = load_config()
    if config is None or config.access_token is None:
        env.logger.error(
            'You need to login into your BeanHub account with "bh login" command first'
        )
        sys.exit(-1)
    return config.access_token.token


@cli.command(help="Sync transactions for all BeanHub Connect banks")
@click.option(
    "-r",
    "--repo",
    type=str,
    help="Name of repository, need to provide it if you have multiple repositories",
)
@pass_env
def sync(env: Environment, repo: str | None):
    token = ensure_token(env)


@cli.command(help="")
@click.option(
    "-r",
    "--repo",
    type=str,
    help="Name of repository, need to provide it if you have multiple repositories",
)
@click.option(
    "-s",
    "--sync",
    type=bool,
    is_flag=True,
    help="Run sync first before running dump",
)
@pass_env
def dump(env: Environment, repo: str, sync: bool):
    token = ensure_token(env)
