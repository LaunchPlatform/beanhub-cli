import click
import uvicorn

from .app.main import make_app
from .cli import cli


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
def server(port: int, host: str, uvicorn_log_level: str):
    app = make_app()
    uvicorn.run(app, port=port, host=host, log_level=uvicorn_log_level)
