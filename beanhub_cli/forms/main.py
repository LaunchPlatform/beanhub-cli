import pathlib
import sys

import click
import uvicorn
from pydantic import ValidationError

from ..context import Context
from ..context import pass_context
from .app.main import make_app
from .cli import cli
from .validator import validate_doc


@cli.command()
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


@cli.command(help="Validate form schema file")
@pass_context
def validate(ctx: Context):
    try:
        form_doc = validate_doc(pathlib.Path.cwd() / ".beanhub" / "forms.yaml")
    except ValidationError as exc:
        ctx.logger.error("Invalid form document with errors:")
        for i, error in enumerate(exc.errors()):
            ctx.logger.error(
                "  errors[%s] type=%s, loc=%s, msg=%s",
                i,
                error["type"],
                error["loc"],
                error["msg"],
            )
        sys.exit(-1)
    except ValueError as exc:
        ctx.logger.error(f"Failed to validate with error: {exc.args[0]}")
        sys.exit(-1)
    ctx.logger.info("Form document is valid, following forms found:")
    for form in form_doc.forms:
        name = form.name
        if form.display_name is not None:
            name = f"{name} ({form.display_name}) "
        ctx.logger.info(
            "  %s (fields=%s)", name, list(map(lambda field: field.name, form.fields))
        )
