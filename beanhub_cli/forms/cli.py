import click

from ..cli import cli as root_cli
from ..context import Context
from ..context import pass_context


@root_cli.group(name="forms")
@pass_context
def cli(ctx: Context):
    pass
