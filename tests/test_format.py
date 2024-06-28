import pathlib

from click.testing import CliRunner

from .helper import switch_cwd
from beanhub_cli.main import cli


def test_format_cmd(tmp_path: pathlib.Path, cli_runner: CliRunner):
    beanhub_dir = tmp_path / ".beanhub"
    beanhub_dir.mkdir()

    bean_file = beanhub_dir / "sample.bean"
    bean_file.write_text("2024-06-27   open   Assets:Cash")

    cli_runner.mix_stderr = False
    with switch_cwd(tmp_path):
        result = cli_runner.invoke(cli, ["format", str(bean_file)])
    assert result.exit_code == 0
    assert bean_file.read_text() == "2024-06-27 open Assets:Cash\n"


def test_format_cmd_without_args(tmp_path: pathlib.Path, cli_runner: CliRunner):
    beanhub_dir = tmp_path / ".beanhub"
    beanhub_dir.mkdir()

    included_bean = beanhub_dir / "mybook.bean"
    included_bean.write_text("2024-06-27   open   Assets:Cash")

    main_bean = beanhub_dir / "main.bean"
    main_bean.write_text('include "mybook.bean"')

    cli_runner.mix_stderr = False
    with switch_cwd(beanhub_dir):
        result = cli_runner.invoke(cli, ["format"])
    assert result.exit_code == 0
    assert included_bean.read_text() == "2024-06-27 open Assets:Cash\n"
