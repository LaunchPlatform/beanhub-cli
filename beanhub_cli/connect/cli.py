from ..aliase import AliasedGroup
from ..cli import cli as root_cli


@root_cli.group(
    name="connect",
    help="BeanHub Connect features, such as sync or dump (login required).",
    cls=AliasedGroup,
)
def cli():
    pass
