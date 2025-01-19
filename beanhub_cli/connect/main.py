import enum
import json
import sys
import tarfile
import tempfile
import time
import urllib.parse

import click
import httpx
import rich
from rich import box
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from ..environment import Environment
from ..environment import pass_env
from ..internal_api import AuthenticatedClient
from ..internal_api.api.connect import create_dump_request
from ..internal_api.api.connect import create_sync_batch
from ..internal_api.api.connect import get_dump_request
from ..internal_api.api.connect import get_sync_batch
from ..internal_api.models import CreateDumpRequestRequest
from ..internal_api.models import CreateDumpRequestResponse
from ..internal_api.models import CreateSyncBatchResponse
from ..internal_api.models import DumpRequestState
from ..internal_api.models import GetDumpRequestResponse
from ..internal_api.models import GetSyncBatchResponse
from ..internal_api.models import PlaidItemSyncState
from ..utils import check_imports
from .cli import cli
from .config import ConnectConfig
from .config import ensure_config
from .encryption import decrypt_file

TABLE_HEADER_STYLE = "yellow"
TABLE_COLUMN_STYLE = "cyan"
SPOOLED_FILE_MAX_SIZE = 1024 * 1024 * 5


GOOD_TERMINAL_SYNC_STATES = frozenset(
    [
        PlaidItemSyncState.IMPORT_COMPLETE,
        PlaidItemSyncState.IMPORT_COMPLETE_NO_CHANGES,
    ]
)
BAD_TERMINAL_SYNC_STATES = frozenset(
    [
        PlaidItemSyncState.IMPORT_FAILED,
        PlaidItemSyncState.SYNC_FAILED,
    ]
)


def run_sync(env: Environment, config: ConnectConfig):
    env.logger.info(
        "Running sync batch for repo [green]%s[/]",
        config.repo,
        extra={"markup": True, "highlighter": None},
    )

    with AuthenticatedClient(base_url=env.api_base_url, token=config.token) as client:
        client.raise_on_unexpected_status = True
        resp: CreateSyncBatchResponse = create_sync_batch.sync(
            username=config.username, repo_name=config.repo, client=client
        )
        batch_id = resp.id
        env.logger.info(
            "Created sync batch [green]%s[/], waiting for updates ...",
            batch_id,
            extra={"markup": True, "highlighter": None},
        )

        while True:
            time.sleep(5)
            resp: GetSyncBatchResponse = get_sync_batch.sync(
                username=config.username,
                repo_name=config.repo,
                sync_batch_id=batch_id,
                client=client,
            )
            total = len(resp.syncs)
            good_terms = list(
                sync
                for sync in resp.syncs
                if PlaidItemSyncState[sync.state.value] in GOOD_TERMINAL_SYNC_STATES
            )
            bad_terms = list(
                sync for sync in resp.syncs if sync.state in BAD_TERMINAL_SYNC_STATES
            )
            progress = len(good_terms) + len(bad_terms)
            if progress >= total:
                break
            else:
                env.logger.info(
                    "Still processing, [green]%s[/] out of [green]%s[/]",
                    progress,
                    total,
                    extra={"markup": True, "highlighter": None},
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
                escape(sync.id),
                escape(sync.item.institution_name),
                escape(sync.state),
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
                escape(sync.item.institution_name),
                escape(sync.state),
                escape(sync.error_message),
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

    with AuthenticatedClient(base_url=env.api_base_url, token=config.token) as client:
        client.raise_on_unexpected_status = True
        resp: CreateDumpRequestResponse = create_dump_request.sync(
            body=CreateDumpRequestRequest(public_key=public_key),
            username=config.username,
            repo_name=config.repo,
            client=client,
        )
        dump_id = resp.id
        env.logger.info(
            "Created dump [green]%s[/] with public_key [green]%s[/], waiting for updates ...",
            dump_id,
            public_key,
            extra={"markup": True, "highlighter": None},
        )

        while True:
            time.sleep(5)
            resp: GetDumpRequestResponse = get_dump_request.sync(
                dump_request_id=dump_id,
                username=config.username,
                repo_name=config.repo,
                client=client,
            )
            if resp.state == DumpRequestState.FAILED:
                env.logger.error("Failed to dump with error: %s", resp.error_message)
                sys.exit(-1)
            elif resp.state == DumpRequestState.COMPLETE:
                break
            else:
                env.logger.debug("State is %s, keep polling...", resp.state)

    download_url = resp.download_url
    sealed_box = SealedBox(private_key)
    encryption_key = json.loads(
        sealed_box.decrypt(URLSafeBase64Encoder.decode(resp.encryption_key))
    )
    key = URLSafeBase64Encoder.decode(encryption_key["key"])
    iv = URLSafeBase64Encoder.decode(encryption_key["iv"])

    with (
        tempfile.SpooledTemporaryFile(SPOOLED_FILE_MAX_SIZE) as encrypted_file,
        tempfile.SpooledTemporaryFile(SPOOLED_FILE_MAX_SIZE) as decrypted_file,
    ):
        with httpx.stream("GET", download_url) as req:
            for chunk in req.iter_bytes():
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
