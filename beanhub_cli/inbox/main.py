import contextlib
import logging
import pathlib
import typing

import click
import yaml
from beanhub_inbox.data_types import InboxDoc
from beanhub_inbox.processor import process_imports
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
@pass_env
def extract(env: Environment, config: str, workdir: str):
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

    for item in process_imports(
        inbox_doc=inbox_doc,
        input_dir=workdir_path,
        think_progress_factory=report_think_progress,
    ):
        pass

    env.logger.info("done")
