from ..config import load_config
from ..environment import Environment
from ..environment import pass_env
from .cli import cli


def ensure_token() -> str:
    pass


@cli.command(help="")
@pass_env
def sync(env: Environment):
    pass
