import enum
import json
import sys
import tarfile
import tempfile
import time
import urllib.parse

import click
import rich
from rich import box
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from ..environment import Environment
from ..environment import pass_env
from ..utils import check_imports
from .cli import cli
from .config import ConnectConfig
from .config import ensure_config
from .encryption import decrypt_file

TABLE_HEADER_STYLE = "yellow"
TABLE_COLUMN_STYLE = "cyan"
SPOOLED_FILE_MAX_SIZE = 1024 * 1024 * 5


@enum.unique
class PlaidItemSyncState(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SYNC_COMPLETE = "SYNC_COMPLETE"
    SYNC_FAILED = "SYNC_FAILED"
    IMPORT_COMPLETE = "IMPORT_COMPLETE"
    IMPORT_COMPLETE_NO_CHANGES = "IMPORT_COMPLETE_NO_CHANGES"
    IMPORT_FAILED = "IMPORT_FAILED"


@enum.unique
class DumpRequestState(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


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


def run_sync(env: Environment, config: ConnectConfig):
    import requests

    env.logger.info(
        "Running sync batch for repo [green]%s[/]",
        config.repo,
        extra={"markup": True, "highlighter": None},
    )
    # TODO: generate API client from OpenAPI spec instead
    url = urllib.parse.urljoin(
        env.api_base_url, f"v1/repos/{config.repo}/connect/sync_batches"
    )
    resp = requests.post(url, headers={"access-token": config.token})
    if resp.status_code == 422:
        env.logger.error("Failed to sync with error: %s", resp.json())
        sys.exit(-1)
    elif resp.status_code == 401:
        env.logger.error(
            "Failed to sync permission error: %s, please ensure your Access Token has API_CONNECT_SYNC permission",
            resp.json(),
        )
        sys.exit(-1)
    resp.raise_for_status()

    batch_id = resp.json()["id"]
    env.logger.info(
        "Created sync batch [green]%s[/], waiting for updates ...",
        batch_id,
        extra={"markup": True, "highlighter": None},
    )

    url = urllib.parse.urljoin(
        env.api_base_url, f"v1/repos/{config.repo}/connect/sync_batches/{batch_id}"
    )
    while True:
        time.sleep(5)
        resp = requests.get(url, headers={"access-token": config.token})
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
            break
        else:
            env.logger.info(
                "Still processing, [green]%s[/] out of [green]%s[/]", progress, total
            )
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


@cli.command(help="Sync transactions for all BeanHub Connect banks")
@click.option(
    "-r",
    "--repo",
    type=str,
    help='Which repository to run sync on, in "<username>/<repo_name>" format',
)
@pass_env
def sync(env: Environment, repo: str | None):
    check_imports(
        logger=env.logger,
        module_names=["requests", "tomli", "tomli_w"],
        required_extras=["login"],
    )
    config = ensure_config(env, repo=repo)
    run_sync(env, config)
    env.logger.info("done")


@cli.command(
    help="Dump transaction CSV files from BeanHub Connect to your local environment"
)
@click.option(
    "-r",
    "--repo",
    type=str,
    help='Which repository to run sync on, in "<username>/<repo_name>" format',
)
@click.option(
    "-s",
    "--sync",
    type=bool,
    is_flag=True,
    help="Run sync first before running dump",
)
@click.option(
    "--unsafe-tar-extract",
    type=bool,
    is_flag=True,
    help="Allow unsafe tar extraction, mostly for Python < 3.11",
)
@pass_env
def dump(env: Environment, repo: str | None, sync: bool, unsafe_tar_extract: bool):
    check_imports(
        logger=env.logger,
        module_names=["requests", "tomli", "tomli_w", "nacl", "cryptography"],
        required_extras=["connect"],
    )

    import requests
    from nacl.encoding import URLSafeBase64Encoder
    from nacl.public import PrivateKey
    from nacl.public import SealedBox

    if not hasattr(tarfile, "data_filter") and not unsafe_tar_extract:
        env.logger.error(
            "You need to use Python >= 3.11 in order to safely unpack the downloaded tar file, or you need to pass "
            "in --unsafe-tar-extract argument to allow unsafe tar file extracting"
        )
        sys.exit(-1)
    config = ensure_config(env, repo=repo)
    if sync:
        run_sync(env, config)

    private_key = PrivateKey.generate()
    public_key = private_key.public_key.encode(URLSafeBase64Encoder).decode("ascii")

    # TODO: generate API client from OpenAPI spec instead
    url = urllib.parse.urljoin(
        env.api_base_url, f"v1/repos/{config.repo}/connect/dumps"
    )
    resp = requests.post(
        url,
        json=dict(public_key=public_key),
        headers={"access-token": config.token},
    )
    if resp.status_code == 422:
        env.logger.error("Failed to dump with error: %s", resp.json())
        sys.exit(-1)
    elif resp.status_code == 401:
        env.logger.error(
            "Failed to dump permission error: %s, please ensure your Access Token has API_CONNECT_DUMP permission",
            resp.json(),
        )
        sys.exit(-1)
    resp.raise_for_status()

    dump_id = resp.json()["id"]
    env.logger.info(
        "Created dump [green]%s[/] with public_key [green]%s[/], waiting for updates ...",
        dump_id,
        public_key,
        extra={"markup": True, "highlighter": None},
    )

    url = urllib.parse.urljoin(
        env.api_base_url, f"v1/repos/{config.repo}/connect/dumps/{dump_id}"
    )
    while True:
        time.sleep(5)
        resp = requests.get(url, headers={"access-token": config.token})
        # TODO: provide friendly error messages here
        resp.raise_for_status()
        payload = resp.json()
        state = DumpRequestState[payload["state"]]
        if state == DumpRequestState.FAILED:
            env.logger.error("Failed to dump with error: %s", payload["error_message"])
            sys.exit(-1)
        elif state == DumpRequestState.COMPLETE:
            break
        else:
            env.logger.debug("State is %s, keep polling...", state)

    download_url = payload["download_url"]
    sealed_box = SealedBox(private_key)
    encryption_key = json.loads(
        sealed_box.decrypt(URLSafeBase64Encoder.decode(payload["encryption_key"]))
    )
    key = URLSafeBase64Encoder.decode(encryption_key["key"])
    iv = URLSafeBase64Encoder.decode(encryption_key["iv"])

    with (
        tempfile.SpooledTemporaryFile(SPOOLED_FILE_MAX_SIZE) as encrypted_file,
        tempfile.SpooledTemporaryFile(SPOOLED_FILE_MAX_SIZE) as decrypted_file,
    ):
        with (requests.get(download_url, stream=True) as req,):
            for chunk in req.iter_content(4096):
                encrypted_file.write(chunk)
        encrypted_file.flush()
        encrypted_file.seek(0)
        env.logger.info("Decrypting downloaded file ...")
        decrypt_file(
            input_file=encrypted_file, output_file=decrypted_file, key=key, iv=iv
        )
        with tarfile.open(fileobj=decrypted_file, mode="r:gz") as tar_file:
            if hasattr(tarfile, "data_filter"):
                tar_file.extractall(filter="data")
            else:
                env.logger.warning("Performing unsafe tar file extracting")
                tar_file.extractall()

    env.logger.info("done")
