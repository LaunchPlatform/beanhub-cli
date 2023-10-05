import click
import uvicorn

from .app.main import make_app
from .cli import cli


@cli.command()
@click.option("--port", default=8080, help="Port number for serving the forms web app.")
def server(port: int):
    app = make_app()
    uvicorn.run(app, port=port, log_level="info")
