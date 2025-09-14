import click
import uvicorn

from ..environment import Environment
from ..environment import pass_env
from .app.main import make_app
from .cli import cli


@cli.command(name="server", help="Run a web server for the MCP service")
@click.option(
    "-p",
    "--port",
    type=int,
    default=8080,
    show_default=True,
    help="Port number for serving the MCP web app.",
)
@click.option(
    "-h",
    "--host",
    type=str,
    default="127.0.0.1",
    show_default=True,
    help="Host for serving the MCP web app.",
)
@click.option(
    "--uvicorn-log-level",
    default="info",
    show_default=True,
    help="Log level for Uvicorn web server.",
)
@pass_env
def run_server(env: Environment, port: int, host: str, uvicorn_log_level: str):
    app = make_app()
    config = uvicorn.Config(app=app, port=port, host=host, log_level=uvicorn_log_level)
    server = uvicorn.Server(config=config)
    server.run()
