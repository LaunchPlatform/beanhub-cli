import json
import logging
import pathlib
import sys
import tarfile
import tempfile
import time
import typing

import click
import httpx
import yaml
from beanhub_inbox.data_types import ArchiveInboxAction
from beanhub_inbox.data_types import ExtractConfig
from beanhub_inbox.data_types import ExtractImportAction
from beanhub_inbox.data_types import IgnoreInboxAction
from beanhub_inbox.data_types import ImportConfig
from beanhub_inbox.data_types import InboxConfig
from beanhub_inbox.data_types import InboxDoc
from beanhub_inbox.data_types import InboxEmail
from beanhub_inbox.data_types import InputConfig
from beanhub_inbox.processor import CSVRowExists
from beanhub_inbox.processor import FinishExtractingColumn
from beanhub_inbox.processor import FinishExtractingRow
from beanhub_inbox.processor import FinishThinking
from beanhub_inbox.processor import IgnoreEmail
from beanhub_inbox.processor import MatchImportRule
from beanhub_inbox.processor import NoMatch
from beanhub_inbox.processor import process_imports
from beanhub_inbox.processor import process_inbox_email
from beanhub_inbox.processor import StartExtractingColumn
from beanhub_inbox.processor import StartProcessingEmail
from beanhub_inbox.processor import StartThinking
from beanhub_inbox.processor import UpdateThinking
from jinja2.sandbox import SandboxedEnvironment
from nacl.encoding import URLSafeBase64Encoder
from nacl.public import PrivateKey
from nacl.public import SealedBox
from rich.json import JSONHighlighter
from rich.live import Live
from rich.panel import Panel

from ..api_helpers import handle_api_exception
from ..auth import AuthConfig
from ..auth import ensure_auth_config
from ..auth import make_auth_client
from ..environment import Environment
from ..environment import pass_env
from ..internal_api.api.inbox import create_inbox_dump_request
from ..internal_api.api.inbox import get_inbox_dump_request
from ..internal_api.api.inbox import get_inbox_emails
from ..internal_api.models import CreateInboxDumpRequest
from ..internal_api.models import CreateInboxDumpRequestResponse
from ..internal_api.models import DumpRequestState
from ..internal_api.models import GetInboxDumpRequestResponse
from ..internal_api.models import GetInboxEmailResponse
from .cli import cli

logger = logging.getLogger(__name__)
SPOOLED_FILE_MAX_SIZE = 1024 * 1024 * 5
DEFAULT_INBOX_CONFIG_FILE = ".beanhub/inbox.yaml"
DEFAULT_INBOX_RULES = [
    InboxConfig(
        action=ArchiveInboxAction(output_file="inbox-data/default/{{ id }}.eml")
    )
]
DEFAULT_INPUT_RULES = [InputConfig(match="inbox-data/default/*.eml")]
DEFAULT_IMPORT_RULES = [
    ImportConfig(
        actions=[
            ExtractImportAction(
                extract=ExtractConfig(output_csv="import-data/inbox/default.csv")
            )
        ]
    )
]
DEFAULT_INBOX_DOC = InboxDoc(
    inbox=DEFAULT_INBOX_RULES,
    inputs=DEFAULT_INPUT_RULES,
    imports=DEFAULT_IMPORT_RULES,
)


def fetch_all_emails(
    env: Environment, config: AuthConfig
) -> typing.Generator[InboxEmail, None, None]:
    with make_auth_client(base_url=env.api_base_url, token=config.token) as client:
        client.raise_on_unexpected_status = True
        current_cursor = None
        while True:
            resp: GetInboxEmailResponse = get_inbox_emails.sync(
                username=config.username,
                repo_name=config.repo,
                client=client,
                cursor=current_cursor,
            )
            if not resp.cursor:
                break
            for email in resp.emails:
                yield InboxEmail(**email.to_dict())
            current_cursor = resp.cursor


def compute_missing_emails(
    inbox_doc: InboxDoc,
    inbox_emails: typing.Sequence[InboxEmail],
    workdir_path: pathlib.Path,
) -> typing.Generator[tuple[InboxEmail, pathlib.Path], None, None]:
    template_env = SandboxedEnvironment()
    workdir = workdir_path.resolve().absolute()
    for inbox_email in inbox_emails:
        action = process_inbox_email(
            template_env=template_env,
            inbox_email=inbox_email,
            inbox_configs=inbox_doc.inbox,
        )
        if action is None:
            continue
        if isinstance(action, IgnoreInboxAction):
            continue
        elif isinstance(action, ArchiveInboxAction):
            output_file = (workdir / action.output_file).resolve().absolute()
            if not output_file.is_relative_to(workdir):
                logger.error(
                    "The email archive output path [green]%s[/] for email [green]%s[/] is not a sub-path of workdir [green]%s[/]",
                    output_file,
                    inbox_email.id,
                    workdir,
                    extra={"markup": True, "highlighter": None},
                )
                sys.exit(-1)
            rel_output_file = output_file.relative_to(workdir)
            if output_file.exists():
                logger.info(
                    "The email [green]%s[/] archive output path [green]%s[/] already exists, skip",
                    inbox_email.id,
                    rel_output_file,
                    extra={"markup": True, "highlighter": None},
                )
                continue
            yield inbox_email, rel_output_file
        else:
            raise ValueError(f"Unexpected action type {type(action)}")


def load_inbox_doc(config: str) -> InboxDoc:
    config_path = pathlib.Path(config)
    if config_path.exists():
        doc_payload = yaml.safe_load(config_path.read_bytes())
        inbox_doc = InboxDoc.model_validate(doc_payload)
        if inbox_doc.inbox is None:
            inbox_doc.inbox = DEFAULT_INBOX_RULES
            logger.info("Use default inbox rules")
        logger.info(
            "Loaded inbox doc from [green]%s[/]",
            config,
            extra={"markup": True, "highlighter": None},
        )
    else:
        inbox_doc = DEFAULT_INBOX_DOC
        logger.info(
            "The inbox doc at [green]%s[/] does not exist, use default config",
            config,
            extra={"markup": True, "highlighter": None},
        )
    logger.debug(
        f"Inbox doc: %s",
        inbox_doc.model_dump_json(indent=2),
        extra={"markup": True, "highlighter": JSONHighlighter()},
    )
    return inbox_doc


@cli.command(
    help="Extract data from archived email files based on rules defined inbox config file"
)
@click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False),
    default=DEFAULT_INBOX_CONFIG_FILE,
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
    workdir_path = pathlib.Path(workdir)
    inbox_doc = load_inbox_doc(config)

    logger.info(
        "Extracting data with Ollama model [green]%s[/]",
        model,
        extra={"markup": True, "highlighter": None},
    )
    debug_output_path = None
    if debug_output_folder is not None:
        debug_output_path = pathlib.Path(debug_output_folder)
        debug_output_path.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Writing debugging files to [magenta]%s[/] folder",
            debug_output_path,
            extra={"markup": True, "highlighter": None},
        )

    inbox_logger = logging.getLogger("beanhub_inbox")
    inbox_logger.setLevel(logging.WARNING)

    # TODO: config logs for inbox lib
    process_event_generators = process_imports(
        inbox_doc=inbox_doc,
        input_dir=workdir_path,
        llm_model=model,
        workdir_path=workdir_path,
    )
    for event in process_event_generators:
        if isinstance(event, StartProcessingEmail):
            logger.info(
                "Processing email [green]%s[/] at [green]%s[/], subject: [blue]%s[/]",
                event.email_file.id,
                event.email_file.filepath,
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
                "Skip processing email [green]%s[/] as the output row exists in the CSV file at [green]%s[/]:[blue]%s[/] already",
                event.email_file.id,
                event.output_csv,
                event.lineno,
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
    logger.info("Done")


@cli.command(help="Dump emails files from BeanHub Inbox to your local environment")
@click.option(
    "-r",
    "--repo",
    type=str,
    help='Which repository to run dump on, in "<username>/<repo_name>" format',
)
@click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False),
    default=DEFAULT_INBOX_CONFIG_FILE,
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
    config: str | None,
    workdir: str,
    unsafe_tar_extract: bool,
):
    workdir_path = pathlib.Path(workdir)
    inbox_doc = load_inbox_doc(config)

    if not hasattr(tarfile, "data_filter") and not unsafe_tar_extract:
        logger.error(
            "You need to use Python >= 3.11 in order to safely unpack the downloaded tar file, or you need to pass "
            "in --unsafe-tar-extract argument to allow unsafe tar file extracting"
        )
        sys.exit(-1)
    config = ensure_auth_config(api_base_url=env.api_base_url, repo=repo)

    inbox_emails = fetch_all_emails(env=env, config=config)
    missing_email_output_files = list(
        compute_missing_emails(
            inbox_doc=inbox_doc, inbox_emails=inbox_emails, workdir_path=workdir_path
        )
    )
    if not missing_email_output_files:
        logger.info("No missing emails found, no need to update")
        return

    private_key = PrivateKey.generate()
    public_key = private_key.public_key.encode(URLSafeBase64Encoder).decode("ascii")

    with make_auth_client(base_url=env.api_base_url, token=config.token) as client:
        client.raise_on_unexpected_status = True
        # TODO: it's a bit slow to download all the emails in one request if there are tons of emails.
        #       maybe it makes more sense to break it down to smaller requests and stream line it?
        resp: CreateInboxDumpRequestResponse = create_inbox_dump_request.sync(
            body=CreateInboxDumpRequest(
                public_key=public_key,
                email_ids=[
                    inbox_email.id for inbox_email, _ in missing_email_output_files
                ],
            ),
            username=config.username,
            repo_name=config.repo,
            client=client,
        )
        dump_id = resp.id
        logger.info(
            "Created dump [green]%s[/] with public_key [green]%s[/], email_count=[green]%s[/], workdir=[green]%s[/], waiting for updates ...",
            dump_id,
            public_key,
            len(missing_email_output_files),
            workdir_path,
            extra={"markup": True, "highlighter": None},
        )

        while True:
            time.sleep(5)
            resp: GetInboxDumpRequestResponse = get_inbox_dump_request.sync(
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
        from ..file_io import extract_inbox_tar

        decrypt_file(
            input_file=encrypted_file, output_file=decrypted_file, key=key, iv=iv
        )
        email_output_paths = {
            inbox_email.id: output_path
            for inbox_email, output_path in missing_email_output_files
        }
        extract_inbox_tar(
            input_file=decrypted_file,
            email_output_paths=email_output_paths,
            workdir_path=workdir_path,
            unsafe_tar_extract=unsafe_tar_extract,
            logger=logger,
        )

    logger.info("done")
