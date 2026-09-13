from click.testing import CliRunner

from beanhub_cli.main import cli


def test_cli_help(cli_runner: CliRunner):
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Command line tools for BeanHub" in result.output
