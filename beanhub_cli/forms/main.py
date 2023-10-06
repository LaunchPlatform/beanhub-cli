import pathlib
import sys

import click
import rich
import uvicorn
from beanhub_forms.data_types.form import FormDoc
from pydantic import ValidationError
from rich import box
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from ..context import Context
from ..context import pass_context
from .app.main import make_app
from .cli import cli
from .validator import enrich_tree
from .validator import errors_to_tree
from .validator import validate_doc


FORM_NAME_STYLE = "green"
FORM_DISPLAY_NAME_STYLE = "bright_black"
TABLE_HEADER_STYLE = "yellow"
TABLE_COLUMN_STYLE = "cyan"


def _validate_form(ctx: Context) -> FormDoc:
    try:
        return validate_doc(pathlib.Path.cwd() / ".beanhub" / "forms.yaml")
    except ValidationError as exc:
        ctx.logger.error("Invalid form document with errors:")
        tree = errors_to_tree(exc.errors())
        rich.print(enrich_tree(tree))
        sys.exit(-1)
    except ValueError as exc:
        ctx.logger.error(f"Failed to validate with error: {exc.args[0]}")
        sys.exit(-1)


@cli.command(help="Validate form schema file")
@pass_context
def validate(ctx: Context):
    _validate_form(ctx)
    rich.print(":white_heavy_check_mark: Form document is valid")


@cli.command(name="list", help="List forms")
@pass_context
def list_forms(ctx: Context):
    form_doc = _validate_form(ctx)
    for form in form_doc.forms:
        form_title = f":downwards_button: [{FORM_NAME_STYLE}]{escape(form.name)}[/{FORM_NAME_STYLE}]"
        if form.display_name:
            form_title += f" [{FORM_DISPLAY_NAME_STYLE}]({escape(form.display_name)})[/{FORM_DISPLAY_NAME_STYLE}]"
        rich.print(form_title)
        table = Table(title="Fields", box=box.SIMPLE, header_style="bold yellow")
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
        rich.print(Padding(table, (1, 0, 1, 4)))


@cli.command(help="Run a web server for form input")
@click.option(
    "-p",
    "--port",
    default=8080,
    show_default=True,
    help="Port number for serving the forms web app.",
)
@click.option(
    "-h",
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Host for serving the forms web app.",
)
@click.option(
    "--uvicorn-log-level",
    default="info",
    show_default=True,
    help="Log level for Uvicorn web server.",
)
@pass_context
def server(ctx: Context, port: int, host: str, uvicorn_log_level: str):
    app = make_app()
    uvicorn.run(app, port=port, host=host, log_level=uvicorn_log_level)
