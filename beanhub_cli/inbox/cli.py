from ..aliase import AliasedGroup
from ..cli import cli as root_cli


@root_cli.group(
    name="inbox",
    help="BeanHub inbox features, such as dump (login required) or extract.",
    cls=AliasedGroup,
)
def cli():
    pass
