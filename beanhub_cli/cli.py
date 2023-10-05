import logging
import os

import click
from beancount_black.formatter import VERBOSE_LOG_LEVEL

LOG_LEVEL_MAP = {
    "verbose": VERBOSE_LOG_LEVEL,
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "fatal": logging.FATAL,
}


@click.group()
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(list(LOG_LEVEL_MAP), case_sensitive=False),
    default=lambda: os.environ.get("LOG_LEVEL", "INFO"),
)
def cli(log_level: str):
    click.echo(f"Log level {log_level}")
