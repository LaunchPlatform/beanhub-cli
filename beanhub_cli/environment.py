import dataclasses
import enum
import logging
import os

import click
from beancount_black.formatter import VERBOSE_LOG_LEVEL


@enum.unique
class LogLevel(enum.Enum):
    VERBOSE = "verbose"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


LOG_LEVEL_MAP = {
    LogLevel.VERBOSE: VERBOSE_LOG_LEVEL,
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.FATAL: logging.FATAL,
}


@dataclasses.dataclass
class Environment:
    log_level: LogLevel = LogLevel.INFO
    logger: logging.Logger = logging.getLogger("beanhub_cli")
    api_base_url: str = os.getenv("BEANHUB_API_URL", "https://api.beanhub.io")


pass_env = click.make_pass_decorator(Environment, ensure=True)
