import contextlib
import json
import logging
import pathlib
import sys
import tarfile
import tempfile
import time

import click
import yaml
from beanhub_inbox.data_types import InboxDoc
from beanhub_inbox.processor import CSVRowExists
from beanhub_inbox.processor import FinishExtractingColumn
from beanhub_inbox.processor import FinishExtractingRow
from beanhub_inbox.processor import FinishThinking
from beanhub_inbox.processor import IgnoreEmail
from beanhub_inbox.processor import MatchImportRule
from beanhub_inbox.processor import NoMatch
from beanhub_inbox.processor import process_imports
from beanhub_inbox.processor import StartExtractingColumn
from beanhub_inbox.processor import StartProcessingEmail
from beanhub_inbox.processor import StartThinking
from beanhub_inbox.processor import UpdateThinking
from rich.json import JSONHighlighter
from rich.live import Live
from rich.panel import Panel

from ..api_helpers import handle_api_exception
from ..auth import AuthConfig
from ..auth import ensure_auth_config
from ..auth import make_auth_client
from ..environment import Environment
from ..environment import pass_env
from .cli import cli

logger = logging.getLogger(__name__)
SPOOLED_FILE_MAX_SIZE = 1024 * 1024 * 5


@contextlib.contextmanager
def report_think_progress():
    with Live(transient=True) as live:
        think_log = ""

        def update(data: str):
            nonlocal think_log
            think_log += data
            live.update(Panel(think_log, title="Thinking ..."))

        yield update


@cli.command(
    help="Extract data from archived email files based on rules defined inbox config file"
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    default=".beanhub/inbox.yaml",
    help="The path to inbox config file",
)
@click.option(
    "-w",
    "--workdir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    default=str(pathlib.Path.cwd()),
    help="The BeanHub project path to work on",
)
@click.option(
    "-m",
    "--model",
    type=str,
    default="phi4",
    help="Which Ollama model to use",
)
@click.option(
    "-k",
    "--keep-thinking-log",
    is_flag=True,
    help="Keep the thinking log on screen after it's done",
)
@click.option(
    "-d",
    "--debug-output-folder",
    type=click.Path(dir_okay=True, file_okay=False, writable=True),
    help="Output files such as prompt and thinking process to the given folder to help debugging",
)
@pass_env
def extract(
    env: Environment,
    config: str,
    workdir: str,
    model: str,
    keep_thinking_log: bool,
    debug_output_folder: str,
):
    config_path = pathlib.Path(config)
    workdir_path = pathlib.Path(workdir)
    debug_output_path = None
    if debug_output_folder is not None:
        debug_output_path = pathlib.Path(debug_output_folder)
        debug_output_path.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        doc_payload = yaml.safe_load(config_path.read_bytes())
        inbox_doc = InboxDoc.model_validate(doc_payload)
        env.logger.info(
            "Loaded inbox doc from [green]%s[/]",
            config,
            extra={"markup": True, "highlighter": None},
        )
    else:
        # TODO: use default
        inbox_doc = None
        env.logger.info(
            "The inbox doc at [green]%s[/] does not exist, use default config",
            config,
            extra={"markup": True, "highlighter": None},
        )

    env.logger.info(
        "Extracting data with Ollama model [green]%s[/]",
        model,
        extra={"markup": True, "highlighter": None},
    )
    progress_output_folder = None
    if debug_output_folder:
        progress_output_folder = pathlib.Path(debug_output_folder)
        env.logger.info(
            "Writing debugging files to [magenta]%s[/] folder",
            progress_output_folder,
            extra={"markup": True, "highlighter": None},
        )

    inbox_logger = logging.getLogger("beanhub_inbox")
    inbox_logger.setLevel(logging.WARNING)

    # TODO: config logs for inbox lib
    process_event_generators = process_imports(
        inbox_doc=inbox_doc,
        input_dir=workdir_path,
        llm_model=model,
        progress_output_folder=progress_output_folder,
        think_progress_factory=report_think_progress,
    )
    for event in process_event_generators:
        if isinstance(event, StartProcessingEmail):
            logger.info(
                "Processing email [green]%s[/] subject: [blue]%s[/]",
                event.email_file.id,
                event.email_file.subject,
                extra={"markup": True, "highlighter": None},
            )
        elif isinstance(event, NoMatch):
            logger.info(
                "No import rule matched for email [green]%s[/]",
                event.email_file.id,
                extra={"markup": True, "highlighter": None},
            )
        elif isinstance(event, MatchImportRule):
            logger.info(
                "Import rule [green]%s[/] matched",
                event.import_config.name
                if event.import_config.name is not None
                else event.import_rule_index,
                extra={"markup": True, "highlighter": None},
            )
        elif isinstance(event, IgnoreEmail):
            logger.info(
                "Ignore email [green]%s[/] as instructed by import action",
                event.email_file.id,
                extra={"markup": True, "highlighter": None},
            )
        elif isinstance(event, CSVRowExists):
            logger.info(
                "Skip processing email [green]%s[/] as it exists in the output CSV file [green]%s[/] already",
                event.email_file.id,
                event.email_file.filepath,
                extra={"markup": True, "highlighter": None},
            )
        elif isinstance(event, StartExtractingColumn):
            logger.info(
                "Extracting column [blue]%s[/]",
                event.column.name,
                extra={"markup": True, "highlighter": None},
            )
        elif isinstance(event, StartThinking):
            if debug_output_path is not None:
                prompt_filepath = (
                    debug_output_path
                    / f"{event.email_file.id}-{event.column.name}-prompt.txt"
                )
                logger.info(
                    "Write prompt to [magenta]%s[/]",
                    prompt_filepath,
                    extra={"markup": True, "highlighter": None},
                )
                prompt_filepath.write_text(event.prompt)

            finish_thinking = None
            with Live(transient=not keep_thinking_log) as live:
                think_log = ""

                for thinking_event in process_event_generators:
                    if isinstance(thinking_event, UpdateThinking):
                        if thinking_event.piece not in ("<think>", "</think>"):
                            think_log += thinking_event.piece
                            from rich.markdown import Markdown

                            live.update(
                                Panel(Markdown(think_log), title="Thinking ...")
                            )
                    elif isinstance(thinking_event, FinishThinking):
                        finish_thinking = thinking_event
                        break
                    else:
                        raise ValueError(
                            f"Unexpected event type {type(thinking_event)}"
                        )

            if debug_output_path is not None:
                thinking_filepath = (
                    debug_output_path
                    / f"{event.email_file.id}-{event.column.name}-thinking.txt"
                )
                logger.info(
                    "Write thinking to [magenta]%s[/]",
                    thinking_filepath,
                    extra={"markup": True, "highlighter": None},
                )
                thinking_filepath.write_text(finish_thinking.thinking)
        elif isinstance(event, FinishExtractingColumn):
            logger.info(
                "  [blue]%s[/] = [green]%s[/]",
                event.column.name,
                event.value,
                extra={"markup": True, "highlighter": None},
            )
        elif isinstance(event, FinishExtractingRow):
            logger.info(
                f"Finished extracting row %s",
                json.dumps(event.row, indent=2),
                extra={"markup": True, "highlighter": JSONHighlighter()},
            )
    env.logger.info("Done")


@cli.command(help="Dump emails files from BeanHub Inbox to your local environment")
@click.option(
    "-r",
    "--repo",
    type=str,
    help='Which repository to run dump on, in "<username>/<repo_name>" format',
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
    config = ensure_auth_config(api_base_url=env.api_base_url, repo=repo)

    # TODO: compare local files and the remote files to determine which emails to pull

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

    logger.info("done")
