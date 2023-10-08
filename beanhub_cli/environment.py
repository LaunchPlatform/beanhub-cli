import dataclasses
import enum
import logging

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


pass_env = click.make_pass_decorator(Environment, ensure=True)
