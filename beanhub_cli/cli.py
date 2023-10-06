import logging
import os

import click

from .context import Context
from .context import LOG_LEVEL_MAP
from .context import LogLevel
from .context import pass_context


@click.group()
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
    click.echo(f"Log level {ctx.log_level.name}")
    ctx.log_level = LogLevel(log_level)
    logging.basicConfig(level=LOG_LEVEL_MAP[ctx.log_level], force=True)
