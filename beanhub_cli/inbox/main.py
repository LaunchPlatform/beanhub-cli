import io
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
from beanhub_inbox.data_types import IgnoreInboxAction
from beanhub_inbox.data_types import InboxDoc
from beanhub_inbox.data_types import InboxEmail
from beanhub_inbox.processor import CSVRowExists
from beanhub_inbox.processor import FinishExtractingColumn
from beanhub_inbox.processor import FinishExtractingRow
from beanhub_inbox.processor import FinishThinking
from beanhub_inbox.processor import IgnoreEmail
from beanhub_inbox.processor import InboxEmail
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
            email=inbox_email,
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


def extract_tar(
    input_file: io.BytesIO,
    email_output_paths: dict[str, pathlib.Path],
    workdir_path: pathlib.Path,
    unsafe_tar_extract: bool,
):
    with tarfile.open(fileobj=input_file, mode="r:gz") as tar_file:
        for member in tar_file:
            if not member.isreg():
                continue
            member_path = pathlib.PurePosixPath(member.name)
            email_id = member_path.stem
            output_path = email_output_paths.get(email_id)
            if output_path is None:
                logger.error("Cannot find output path for email %s", email_id)
                sys.exit(-1)
            output_path.parent.mkdir(exist_ok=True, parents=True)
            logger.info(
                "Writing email [green]%s[/] to [green]%s[/]",
                email_id,
                output_path,
                extra={"markup": True, "highlighter": None},
            )
            full_output_path = workdir_path / output_path
            has_data_filter = hasattr(tarfile, "data_filter")
            if not has_data_filter and not unsafe_tar_extract:
                logger.error(
                    "You need to use Python >= 3.11 in order to safely unpack the downloaded tar file, or you need to pass "
                    "in --unsafe-tar-extract argument to allow unsafe tar file extracting"
                )
                sys.exit(-1)
            member.name = output_path.name
            tar_file.extract(
                member,
                full_output_path.parent,
                set_attrs=False,
                filter="data" if has_data_filter else None,
            )


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
    debug_output_path = None
    if debug_output_folder is not None:
        debug_output_path = pathlib.Path(debug_output_folder)
        debug_output_path.mkdir(parents=True, exist_ok=True)
        env.logger.info(
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
                "Skip processing email [green]%s[/] as it exists in the output CSV file at [green]%s[/]:[blue]%s[/] already",
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
    env.logger.info("Done")


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
    default_config_path = pathlib.Path(DEFAULT_INBOX_CONFIG_FILE)
    if config is not None or default_config_path.exists():
        if config is not None:
            config_path = pathlib.Path(config)
            if not config_path.exists():
                logger.error("Inbox config file does not exist at %s", config_path)
                sys.exit(-1)
        else:
            config_path = default_config_path
        with config_path.open("rt") as fo:
            doc_payload = yaml.safe_load(fo)
        inbox_doc = InboxDoc.model_validate(doc_payload)
        env.logger.info(
            "Loaded inbox doc from [green]%s[/]",
            config,
            extra={"markup": True, "highlighter": None},
        )
    else:
        env.logger.info(
            "Loaded default inbox doc as config file is not provided by argument and does exists at the default location %s",
            default_config_path,
        )
        # TODO: load default
        inbox_doc = None

    workdir_path = pathlib.Path(workdir)

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

        decrypt_file(
            input_file=encrypted_file, output_file=decrypted_file, key=key, iv=iv
        )
        email_output_paths = {
            inbox_email.id: output_path
            for inbox_email, output_path in missing_email_output_files
        }
        extract_tar(
            input_file=decrypted_file,
            email_output_paths=email_output_paths,
            workdir_path=workdir_path,
            unsafe_tar_extract=unsafe_tar_extract,
        )

    logger.info("done")
