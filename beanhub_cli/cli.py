import logging
import os

import click
from rich.logging import RichHandler

from .aliase import AliasedGroup
from .context import Context
from .context import LOG_LEVEL_MAP
from .context import LogLevel
from .context import pass_context


@click.group(help="Command line tools for BeanHub", cls=AliasedGroup)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(
        list(map(lambda key: key.value, LOG_LEVEL_MAP.keys())), case_sensitive=False
    ),
    default=lambda: os.environ.get("LOG_LEVEL", "INFO"),
)
@pass_context
def cli(ctx: Context, log_level: str):
    FORMAT = "%(message)s"
    logging.basicConfig(
        level=LOG_LEVEL_MAP[ctx.log_level],
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler()],
        force=True,
    )
    ctx.log_level = LogLevel(log_level)
