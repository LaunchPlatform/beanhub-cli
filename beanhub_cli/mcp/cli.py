from ..aliase import AliasedGroup
from ..cli import cli as root_cli


@root_cli.group(
    name="form",
    help="Validating BeanHub Forms and running a simple web app.",
    cls=AliasedGroup,
)
def cli():
    pass
