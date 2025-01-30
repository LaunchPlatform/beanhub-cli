import json
import logging
import pathlib
import sys
import tarfile
import tempfile
import time

import click
import rich
from rich import box
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from ..api_helpers import handle_api_exception
from ..api_helpers import make_auth_client
from ..environment import Environment
from ..environment import pass_env
from ..utils import check_imports
from ..utils import ExtraDepsSet
from .cli import cli
from .config import ConnectConfig
from .config import ensure_config

logger = logging.getLogger(__name__)

TABLE_HEADER_STYLE = "yellow"
TABLE_COLUMN_STYLE = "cyan"
SPOOLED_FILE_MAX_SIZE = 1024 * 1024 * 5


def run_sync(env: Environment, config: ConnectConfig):
    from ..internal_api.api.connect import create_sync_batch
    from ..internal_api.api.connect import get_sync_batch
    from ..internal_api.models import CreateSyncBatchResponse
    from ..internal_api.models import GetSyncBatchResponse
    from ..internal_api.models import HTTPValidationError
    from ..internal_api.models import PlaidItemSyncState

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

    logger.info(
        "Running sync batch for repo [green]%s[/]",
        config.repo,
        extra={"markup": True, "highlighter": None},
    )

    with make_auth_client(base_url=env.api_base_url, token=config.token) as client:
        client.raise_on_unexpected_status = True
        resp: CreateSyncBatchResponse = create_sync_batch.sync(
            username=config.username, repo_name=config.repo, client=client
        )
        if isinstance(resp, HTTPValidationError):
            logger.error(
                "Failed to create sync batch with error: %s",
                resp.additional_properties.get("error", resp.detail),
            )
            sys.exit(-1)
        batch_id = resp.id
        logger.info(
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
                logger.info(
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
                escape(sync.id),
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
@check_imports(ExtraDepsSet.LOGIN, logger)
@handle_api_exception(logger)
def sync(env: Environment, repo: str | None):
    config = ensure_config(api_base_url=env.api_base_url, repo=repo)
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
    "--output-accounts",
    type=click.Path(writable=True),
    help="File path of Bank accounts CSV file to write to, if a folder is provided, default filename accounts.csv will be used",
)
@click.option(
    "--unsafe-tar-extract",
    type=bool,
    is_flag=True,
    help="Allow unsafe tar extraction, mostly for Python < 3.11",
)
@pass_env
@check_imports(ExtraDepsSet.CONNECT, logger)
@handle_api_exception(logger)
def dump(
    env: Environment,
    repo: str | None,
    sync: bool,
    output_accounts: str | None,
    unsafe_tar_extract: bool,
):
    import httpx
    from ..internal_api.api.connect import create_dump_request
    from ..internal_api.api.connect import get_dump_request
    from ..internal_api.models import CreateDumpRequestRequest
    from ..internal_api.models import CreateDumpRequestResponse
    from ..internal_api.models import DumpRequestState
    from ..internal_api.models import GetDumpRequestResponse
    from nacl.encoding import URLSafeBase64Encoder
    from nacl.public import PrivateKey
    from nacl.public import SealedBox

    if not hasattr(tarfile, "data_filter") and not unsafe_tar_extract:
        logger.error(
            "You need to use Python >= 3.11 in order to safely unpack the downloaded tar file, or you need to pass "
            "in --unsafe-tar-extract argument to allow unsafe tar file extracting"
        )
        sys.exit(-1)
    config = ensure_config(api_base_url=env.api_base_url, repo=repo)
    if sync:
        run_sync(env, config)

    private_key = PrivateKey.generate()
    public_key = private_key.public_key.encode(URLSafeBase64Encoder).decode("ascii")

    with make_auth_client(base_url=env.api_base_url, token=config.token) as client:
        client.raise_on_unexpected_status = True
        resp: CreateDumpRequestResponse = create_dump_request.sync(
            body=CreateDumpRequestRequest(
                public_key=public_key, output_accounts=output_accounts is not None
            ),
            username=config.username,
            repo_name=config.repo,
            client=client,
        )
        dump_id = resp.id
        logger.info(
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
                logger.error("Failed to dump with error: %s", resp.error_message)
                sys.exit(-1)
            elif resp.state == DumpRequestState.COMPLETE:
                break
            else:
                logger.debug("State is %s, keep polling...", resp.state)

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
        logger.info("Decrypting downloaded file ...")

        # delay import for testing purpose
        from .encryption import decrypt_file
        from .file_io import extract_tar

        decrypt_file(
            input_file=encrypted_file, output_file=decrypted_file, key=key, iv=iv
        )
        extract_tar(input_file=decrypted_file, logger=env.logger)

    if output_accounts is not None and resp.accounts_download_url is not None:
        output_accounts = pathlib.Path(output_accounts)
        if output_accounts.is_dir():
            output_accounts_path = output_accounts / "accounts.csv"
        else:
            output_accounts_path = output_accounts
        with (
            tempfile.SpooledTemporaryFile(SPOOLED_FILE_MAX_SIZE) as encrypted_file,
            output_accounts_path.open("wb") as decrypted_file,
        ):
            with httpx.stream("GET", resp.accounts_download_url) as req:
                for chunk in req.iter_bytes():
                    encrypted_file.write(chunk)
            encrypted_file.flush()
            encrypted_file.seek(0)
            logger.info(
                "Decrypting downloaded accounts file to %s ...", output_accounts_path
            )

            # delay import for testing purpose
            from .encryption import decrypt_file
            from .file_io import extract_tar

            decrypt_file(
                input_file=encrypted_file, output_file=decrypted_file, key=key, iv=iv
            )

    logger.info("done")
