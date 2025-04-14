import logging

from ..environment import Environment
from ..environment import pass_env
from .cli import cli

logger = logging.getLogger(__name__)


@cli.command(
    help='Extract data from archived email files based on rules defined in the ".beanhub/inbox.yaml" file'
)
@pass_env
def extract(env: Environment):
    env.logger.info("done")
