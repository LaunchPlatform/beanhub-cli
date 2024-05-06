from . import format  # noqa
from .cli import cli
from .forms import main as forms  # noqa
from .import_cli import main as import_cli  # noqa

__ALL__ = [cli]

if __name__ == "__main__":
    cli()
