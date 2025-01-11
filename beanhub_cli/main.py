from . import format  # noqa
from .cli import cli
from .connect import main as connect  # noqa
from .forms import main as forms  # noqa
from .import_cli import main as import_cli  # noqa
from .login import main as login  # noqa

__ALL__ = [cli]

if __name__ == "__main__":
    cli()
