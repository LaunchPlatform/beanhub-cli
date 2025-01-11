import sys
import time
import urllib.parse

import click
import requests

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
@pass_env
def sync(env: Environment):
    token = ensure_token(env)

    # XXX:
    username = "fangpenlin"
    repo = "mybook"

    url = urllib.parse.urljoin(
        env.api_base_url, f"v1/repos/{username}/{repo}/connect/sync_batches"
    )
    resp = requests.post(url, headers={"access-token": token})
    # TODO: provide friendly error messages here
    resp.raise_for_status()
    batch_id = resp.json()["id"]
    env.logger.info("Created sync batch %s, waiting for updates ...", batch_id)

    url = urllib.parse.urljoin(
        env.api_base_url, f"v1/repos/{username}/{repo}/connect/sync_batches/{batch_id}"
    )
    while True:
        time.sleep(5)
        resp = requests.get(url, headers={"access-token": token})
        # TODO: provide friendly error messages here
        resp.raise_for_status()
        print("@" * 10, resp.json())


@cli.command(help="")
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
