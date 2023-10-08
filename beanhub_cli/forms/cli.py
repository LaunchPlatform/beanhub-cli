from click import pass_context as pass_click_context
from click.core import Context as ClickContext

from ..aliase import AliasedGroup
from ..cli import cli as root_cli
from ..environment import Environment
from ..environment import pass_env


@root_cli.group(
    name="form",
    help="Validating BeanHub Forms and running a simple web app.",
    context_settings=dict(obj="bar"),
    cls=AliasedGroup,
)
@pass_env
@pass_click_context
def cli(ctx: Environment, click_context: ClickContext):
    pass
