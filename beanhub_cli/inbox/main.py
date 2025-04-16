import contextlib
import json
import logging
import pathlib
import typing

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
from rich.json import JSON
from rich.json import JSONHighlighter
from rich.live import Live
from rich.panel import Panel
from rich.status import Status

from ..environment import Environment
from ..environment import pass_env
from .cli import cli

logger = logging.getLogger(__name__)


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
    "--debug-output-folder",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Output files such as prompt and thinking process to the given folder to help debugging",
)
@pass_env
def extract(
    env: Environment, config: str, workdir: str, model: str, debug_output_folder: str
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
    progress_output_folder = None
    if debug_output_folder:
        progress_output_folder = pathlib.Path(debug_output_folder)
        env.logger.info("Writing debugging files to %s folder", progress_output_folder)

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
                "Processing email [green]%s[/]",
                event.email_file.id,
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
            with Live(transient=True) as live:
                think_log = ""

                for thinking_event in process_event_generators:
                    if isinstance(thinking_event, UpdateThinking):
                        think_log += thinking_event.piece
                        live.update(Panel(think_log, title="Thinking ..."))
                    elif isinstance(thinking_event, FinishThinking):
                        # TODO:
                        break
                    else:
                        raise ValueError(
                            f"Unexpected event type {type(thinking_event)}"
                        )
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
