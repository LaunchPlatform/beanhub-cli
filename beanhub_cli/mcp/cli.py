from ..aliase import AliasedGroup
from ..cli import cli as root_cli


@root_cli.group(
    name="mcp",
    help="Run Model Context Protocol (MCP) server for LLM to access your Beancount books",
)
def cli():
    pass
