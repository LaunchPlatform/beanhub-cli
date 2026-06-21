import json
import logging
import pathlib
import sys
import tarfile
import tempfile
import time
from collections.abc import Callable

import click
import httpx
import rich
from nacl.encoding import URLSafeBase64Encoder
from nacl.public import PrivateKey
from nacl.public import SealedBox
from rich import box
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from ..api_helpers import handle_api_exception
from ..auth import AuthConfig
from ..auth import ensure_auth_config
from ..auth import make_auth_client
from ..environment import Environment
from ..environment import pass_env
from ..internal_api.api.connect import create_dump_request
from ..internal_api.api.connect import create_sync_batch
from ..internal_api.api.connect import get_dump_request
from ..internal_api.api.connect import get_sync_batch
from ..internal_api.models import CreateDumpRequestRequest
from ..internal_api.models import CreateDumpRequestResponse
from ..internal_api.models import CreateSyncBatchRequest
from ..internal_api.models import CreateSyncBatchResponse
from ..internal_api.models import DumpRequestState
from ..internal_api.models import GetDumpRequestResponse
from ..internal_api.models import GetSyncBatchResponse
from ..internal_api.models import HTTPValidationError
from ..internal_api.models import PlaidItemSyncState
from ..internal_api.models import RepositoryType
from ..internal_api.models import SyncBatchState
from ..internal_api.types import Unset
from .cli import cli

logger = logging.getLogger(__name__)

TABLE_HEADER_STYLE = "yellow"
TABLE_COLUMN_STYLE = "cyan"
SPOOLED_FILE_MAX_SIZE = 1024 * 1024 * 5

CONNECT_ONLY_IMPORT_AND_COMMIT_ERROR = (
    "Import and commit is only available for Git repositories. "
    "Connect repositories only support syncing transactions and "
    "exporting data."
)
TERMINAL_BATCH_STATES = frozenset(
    [
        SyncBatchState.IMPORT_COMPLETE,
        SyncBatchState.IMPORT_COMPLETE_NO_CHANGES,
        SyncBatchState.IMPORT_FAILED,
        SyncBatchState.SYNC_COMPLETE,
    ]
)
SUCCESS_SYNC_STATES = frozenset(
    [
        PlaidItemSyncState.SYNC_COMPLETE,
        PlaidItemSyncState.SYNC_COMPLETE_ONLY,
        PlaidItemSyncState.IMPORT_COMPLETE,
        PlaidItemSyncState.IMPORT_COMPLETE_NO_CHANGES,
    ]
)
BAD_TERMINAL_SYNC_STATES = frozenset(
    [
        PlaidItemSyncState.IMPORT_FAILED,
        PlaidItemSyncState.SYNC_FAILED,
        PlaidItemSyncState.SKIPPED,
    ]
)
SUCCESS_BATCH_STATES = frozenset(
    [
        SyncBatchState.SYNC_COMPLETE,
        SyncBatchState.IMPORT_COMPLETE,
        SyncBatchState.IMPORT_COMPLETE_NO_CHANGES,
    ]
)


def _get_repository_type(
    client, username: str, repo_name: str
) -> RepositoryType | None:
    from ..internal_api.api.repo import list_repo

    resp = list_repo.sync(client=client)
    for repository in resp.repositories:
        if repository.username == username and repository.name == repo_name:
            return repository.type_
    return None


def _format_validation_error(resp: HTTPValidationError) -> str:
    error = resp.additional_properties.get("error")
    if error is not None:
        return str(error)
    if resp.detail:
        return str(resp.detail)
    return "Unknown validation error"


def _sync_state_label(state: PlaidItemSyncState) -> str:
    return state.value


def _sync_error_message(error_message: str | None | Unset) -> str:
    if isinstance(error_message, Unset) or error_message is None:
        return ""
    return error_message


def _classify_syncs(resp: GetSyncBatchResponse) -> tuple[list, list]:
    bad_terms = [sync for sync in resp.syncs if sync.state in BAD_TERMINAL_SYNC_STATES]
    good_terms = [sync for sync in resp.syncs if sync.state in SUCCESS_SYNC_STATES]
    if resp.state in SUCCESS_BATCH_STATES:
        classified_ids = {id(sync) for sync in good_terms} | {
            id(sync) for sync in bad_terms
        }
        good_terms.extend(sync for sync in resp.syncs if id(sync) not in classified_ids)
    return good_terms, bad_terms


def _print_sync_table(
    *,
    title: str,
    syncs: list,
    columns: list[tuple[str, Callable[..., str]]],
):
    if not syncs:
        return

    table = Table(
        title=title,
        box=box.SIMPLE,
        header_style=TABLE_HEADER_STYLE,
        expand=True,
    )
    for column_name, _ in columns:
        table.add_column(column_name, style=TABLE_COLUMN_STYLE)
    for sync in syncs:
        table.add_row(
            *[escape(formatter(sync)) for _, formatter in columns],
        )
    rich.print(Padding(table, (1, 0, 0, 4)))


def run_sync(env: Environment, config: AuthConfig, import_and_commit: bool = False):
    logger.info(
        "Running sync batch for repo [green]%s[/]",
        config.repo,
        extra={"markup": True, "highlighter": None},
    )

    with make_auth_client(base_url=env.api_base_url, token=config.token) as client:
        client.raise_on_unexpected_status = True
        if import_and_commit:
            repo_type = _get_repository_type(client, config.username, config.repo)
            if repo_type == RepositoryType.CONNECT:
                logger.error(CONNECT_ONLY_IMPORT_AND_COMMIT_ERROR)
                sys.exit(-1)

        resp: CreateSyncBatchResponse = create_sync_batch.sync(
            username=config.username,
            repo_name=config.repo,
            client=client,
            body=CreateSyncBatchRequest(import_and_commit=import_and_commit),
        )
        if isinstance(resp, HTTPValidationError):
            logger.error(
                "Failed to create sync batch with error: %s",
                _format_validation_error(resp),
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
            if resp.state in TERMINAL_BATCH_STATES:
                break
            logger.info(
                "Batch state is [green]%s[/], still processing ...",
                resp.state.value,
                extra={"markup": True, "highlighter": None},
            )

        if import_and_commit:
            if resp.state == SyncBatchState.IMPORT_FAILED:
                logger.error(
                    "Batch import and commit failed with error: %s",
                    resp.error_message,
                )
                sys.exit(-1)
            if resp.state in (
                SyncBatchState.IMPORT_COMPLETE,
                SyncBatchState.IMPORT_COMPLETE_NO_CHANGES,
            ):
                logger.info(
                    "Batch import and commit finished with state [green]%s[/]",
                    resp.state.value,
                    extra={"markup": True, "highlighter": None},
                )

        good_terms, bad_terms = _classify_syncs(resp)
        _print_sync_table(
            title="Sync finished successfully",
            syncs=good_terms,
            columns=[
                ("Id", lambda sync: sync.id),
                ("Institution", lambda sync: sync.item.institution_name),
                ("State", lambda sync: _sync_state_label(sync.state)),
            ],
        )
        _print_sync_table(
            title="Sync finished with error",
            syncs=bad_terms,
            columns=[
                ("Id", lambda sync: sync.id),
                ("Institution", lambda sync: sync.item.institution_name),
                ("State", lambda sync: _sync_state_label(sync.state)),
                ("Error", lambda sync: _sync_error_message(sync.error_message)),
            ],
        )


@cli.command(help="Sync transactions for all BeanHub Connect banks")
@click.option(
    "-r",
    "--repo",
    type=str,
    help='Which repository to run sync on, in "<username>/<repo_name>" format',
)
@click.option(
    "-i",
    "--import",
    "import_",
    is_flag=True,
    help=(
        "After syncing all banks, run BeanHub Import and commit the changes to "
        "the Git repository. Only available for Git repositories; not supported "
        "for Connect-only repositories, which have no Git repo."
    ),
)
@pass_env
@handle_api_exception(logger)
def sync(env: Environment, repo: str | None, import_: bool):
    config = ensure_auth_config(api_base_url=env.api_base_url, repo=repo)
    run_sync(env, config, import_and_commit=import_)
    env.logger.info("done")


@cli.command(
    help="Dump transaction CSV files from BeanHub Connect to your local environment"
)
@click.option(
    "-r",
    "--repo",
    type=str,
    help='Which repository to run dump on, in "<username>/<repo_name>" format',
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
@handle_api_exception(logger)
def dump(
    env: Environment,
    repo: str | None,
    sync: bool,
    output_accounts: str | None,
    unsafe_tar_extract: bool,
):
    if not hasattr(tarfile, "data_filter") and not unsafe_tar_extract:
        logger.error(
            "You need to use Python >= 3.11 in order to safely unpack the downloaded tar file, or you need to pass "
            "in --unsafe-tar-extract argument to allow unsafe tar file extracting"
        )
        sys.exit(-1)
    config = ensure_auth_config(api_base_url=env.api_base_url, repo=repo)
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
        from ..encryption import decrypt_file
        from ..file_io import extract_tar

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
            from ..encryption import decrypt_file
            from ..file_io import extract_tar

            decrypt_file(
                input_file=encrypted_file, output_file=decrypted_file, key=key, iv=iv
            )

    logger.info("done")
