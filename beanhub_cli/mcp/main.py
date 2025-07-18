import pathlib
import socket
import typing
import webbrowser

import click
import rich
import uvicorn
import yaml.parser
import yaml.scanner
from beanhub_forms.data_types.form import FormDoc
from click import get_current_context
from pydantic import ValidationError
from rich import box
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from ..environment import Environment
from ..environment import pass_env
from .app.main import make_app
from .cli import cli
from .validator import enrich_tree
from .validator import errors_to_tree
from .validator import validate_doc


FORM_NAME_STYLE = "green"
FORM_DISPLAY_NAME_STYLE = "bright_black"
TABLE_HEADER_STYLE = "yellow"
TABLE_COLUMN_STYLE = "cyan"


class StartupCallbackServer(uvicorn.Server):
    def __init__(self, config: uvicorn.Config, startup_callback: typing.Callable):
        super().__init__(config)
        self.startup_callback = startup_callback

    async def startup(
        self, sockets: typing.Optional[list[socket.socket]] = None
    ) -> None:
        await super().startup()
        self.startup_callback()


def _validate_form(env: Environment) -> FormDoc:
    ctx = get_current_context()
    try:
        return validate_doc(pathlib.Path.cwd() / ".beanhub" / "forms.yaml")
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as exc:
        env.logger.error("Invalid form document with YAML errors:")
        rich.print(str(exc))
        ctx.exit(-1)
    except ValidationError as exc:
        env.logger.error("Invalid form document with errors:")
        tree = errors_to_tree(exc.errors())
        rich.print(enrich_tree(tree))
        ctx.exit(-1)
    except ValueError as exc:
        env.logger.error(f"Failed to validate with error: {exc.args[0]}")
        ctx.exit(-1)


@cli.command(help="Validate form schema file")
@pass_env
def validate(env: Environment):
    _validate_form(env)
    rich.print(":white_heavy_check_mark: Form document is valid")


@cli.command(name="list", help="List forms")
@pass_env
def list_forms(env: Environment):
    form_doc = _validate_form(env)
    for form in form_doc.forms:
        form_title = f":downwards_button: [{FORM_NAME_STYLE}]{escape(form.name)}[/{FORM_NAME_STYLE}]"
        if form.display_name:
            form_title += f" [{FORM_DISPLAY_NAME_STYLE}]({escape(form.display_name)})[/{FORM_DISPLAY_NAME_STYLE}]"
        rich.print(form_title)

        table = Table(
            title="Fields", box=box.SIMPLE, header_style=TABLE_HEADER_STYLE, expand=True
        )
        table.add_column("Name", style=TABLE_COLUMN_STYLE)
        table.add_column("Display Name", style=TABLE_COLUMN_STYLE)
        table.add_column("Type", style=TABLE_COLUMN_STYLE)
        table.add_column("Required", style=TABLE_COLUMN_STYLE)
        table.add_column("Default", style=TABLE_COLUMN_STYLE)
        for field in form.fields:
            table.add_row(
                escape(field.name),
                escape(field.display_name) if field.display_name else None,
                escape(field.type.value),
                str(field.required),
                escape(field.default) if field.default else None,
            )
        rich.print(Padding(table, (1, 0, 0, 4)))

        table = Table(
            title="Operations",
            box=box.SIMPLE,
            header_style=TABLE_HEADER_STYLE,
            expand=True,
        )
        table.add_column("Type", style=TABLE_COLUMN_STYLE)
        table.add_column("File", style=TABLE_COLUMN_STYLE)
        table.add_column("Content", style=TABLE_COLUMN_STYLE)
        for operation in form.operations:
            table.add_row(
                escape(operation.type),
                escape(operation.file),
                escape(operation.content),
            )
        rich.print(Padding(table, (1, 0, 0, 4)))


@cli.command(name="server", help="Run a web server for form input")
@click.option(
    "-p",
    "--port",
    type=int,
    default=8080,
    show_default=True,
    help="Port number for serving the forms web app.",
)
@click.option(
    "-h",
    "--host",
    type=str,
    default="127.0.0.1",
    show_default=True,
    help="Host for serving the forms web app.",
)
@click.option(
    "-o",
    "--open-browser",
    default=True,
    type=bool,
    help="Open a new tab in the browser or not.",
)
@click.option(
    "--uvicorn-log-level",
    default="info",
    show_default=True,
    help="Log level for Uvicorn web server.",
)
@pass_env
def run_server(
    env: Environment, port: int, host: str, open_browser: bool, uvicorn_log_level: str
):
    app = make_app()

    def after_startup():
        if open_browser:
            url = f"http://{host}:{port}"
            env.logger.info("Opening URL %s in the browser", url)
            webbrowser.open(url)

    config = uvicorn.Config(app=app, port=port, host=host, log_level=uvicorn_log_level)
    server = StartupCallbackServer(config=config, startup_callback=after_startup)
    server.run()
