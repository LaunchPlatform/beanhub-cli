import enum
import sys
import time
import urllib.parse

import click
import requests
import rich
from rich import box
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from ..config import load_config
from ..environment import Environment
from ..environment import pass_env
from .cli import cli

TABLE_HEADER_STYLE = "yellow"
TABLE_COLUMN_STYLE = "cyan"


@enum.unique
class PlaidItemSyncState(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SYNC_COMPLETE = "SYNC_COMPLETE"
    SYNC_FAILED = "SYNC_FAILED"
    IMPORT_COMPLETE = "IMPORT_COMPLETE"
    IMPORT_COMPLETE_NO_CHANGES = "IMPORT_COMPLETE_NO_CHANGES"
    IMPORT_FAILED = "IMPORT_FAILED"


GOOD_TERMINAL_SYNC_STATES = frozenset(
    [
        PlaidItemSyncState.IMPORT_COMPLETE,
        PlaidItemSyncState.IMPORT_COMPLETE_NO_CHANGES,
    ]
)
BAD_TERMINAL_SYNC_STATES = frozenset(
    [
        PlaidItemSyncState.IMPORT_FAILED,
    ]
)


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
    if resp.status_code == 422:
        env.logger.error("Failed to sync with error: %s", resp.json())
        sys.exit(-1)
    resp.raise_for_status()

    batch_id = resp.json()["id"]
    env.logger.info(
        "Created sync batch [green]%s[/], waiting for updates ...",
        batch_id,
        extra={"markup": True, "highlighter": None},
    )

    url = urllib.parse.urljoin(
        env.api_base_url, f"v1/repos/{username}/{repo}/connect/sync_batches/{batch_id}"
    )
    while True:
        time.sleep(5)
        resp = requests.get(url, headers={"access-token": token})
        # TODO: provide friendly error messages here
        resp.raise_for_status()
        payload = resp.json()
        total = len(payload["syncs"])
        good_terms = list(
            sync
            for sync in payload["syncs"]
            if PlaidItemSyncState[sync["state"]] in GOOD_TERMINAL_SYNC_STATES
        )
        bad_terms = list(
            sync
            for sync in payload["syncs"]
            if PlaidItemSyncState[sync["state"]] in BAD_TERMINAL_SYNC_STATES
        )
        progress = len(good_terms) + len(bad_terms)
        if progress >= total:
            table = Table(
                title="Sync finished successfully",
                box=box.SIMPLE,
                header_style=TABLE_HEADER_STYLE,
                expand=True,
            )
            table.add_column("Id", style=TABLE_COLUMN_STYLE)
            table.add_column("Institution", style=TABLE_COLUMN_STYLE)
            table.add_column("State", style=TABLE_COLUMN_STYLE)
            for sync in good_terms:
                table.add_row(
                    escape(sync["id"]),
                    escape(sync["item"]["institution_name"]),
                    escape(sync["state"]),
                )
            rich.print(Padding(table, (1, 0, 0, 4)))

            table = Table(
                title="Sync finished with error",
                box=box.SIMPLE,
                header_style=TABLE_HEADER_STYLE,
                expand=True,
            )
            table.add_column("Id", style=TABLE_COLUMN_STYLE)
            table.add_column("Institution", style=TABLE_COLUMN_STYLE)
            table.add_column("State", style=TABLE_COLUMN_STYLE)
            table.add_column("Error", style=TABLE_COLUMN_STYLE)
            for sync in bad_terms:
                table.add_row(
                    escape(sync["id"]),
                    escape(sync["item"]["institution_name"]),
                    escape(sync["state"]),
                    escape(sync["error_message"]),
                )
            rich.print(Padding(table, (1, 0, 0, 4)))

            env.logger.info("done")
            break
        env.logger.info(
            "Still processing, [green]%s[/] out of [green]%s[/]", progress, total
        )


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
