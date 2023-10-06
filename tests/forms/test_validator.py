import contextlib
import os
import pathlib

import pytest
import yaml
from beanhub_forms.data_types.form import FormDoc
from click.testing import CliRunner
from pydantic import ValidationError

from beanhub_cli.forms.validator import validate_doc
from beanhub_cli.main import cli


@contextlib.contextmanager
def switch_cwd(cwd: pathlib.Path):
    current_cwd = pathlib.Path.cwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(current_cwd)


def test_file_does_not_exist(tmp_path: pathlib.Path):
    doc_file = tmp_path / "does-not-exists.yaml"
    with pytest.raises(ValueError) as exc:
        validate_doc(doc_file)
    assert exc.value.args[0] == f"Form document at {doc_file} does not exist"


@pytest.mark.parametrize(
    "schema, expected_errors",
    [
        (
            {},
            [
                {
                    "type": "missing",
                    "loc": ("forms",),
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                }
            ],
        ),
        (
            dict(forms=[dict()]),
            [
                {
                    "type": "missing",
                    "loc": ("forms", 0, "name"),
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ("forms", 0, "fields"),
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ("forms", 0, "operations"),
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
            ],
        ),
    ],
)
def test_bad_schema(tmp_path: pathlib.Path, schema: dict, expected_errors: list):
    doc_file = tmp_path / "forms.yaml"
    with doc_file.open("wt") as fo:
        yaml.dump(schema, fo)
    with pytest.raises(ValidationError) as exc:
        validate_doc(doc_file)
    assert exc.value.errors() == expected_errors


def test_validate_cmd(tmp_path: pathlib.Path, cli_runner: CliRunner):
    beanhub_dir = tmp_path / ".beanhub"
    beanhub_dir.mkdir()
    form_doc = beanhub_dir / "forms.yaml"
    doc = FormDoc(forms=[])
    form_doc.write_text(yaml.dump(FormDoc.model_dump(doc)))

    cli_runner.mix_stderr = False
    with switch_cwd(tmp_path):
        result = cli_runner.invoke(cli, ["form", "validate"])
    assert result.exit_code == 0
    assert "Form document is valid" in result.stderr


def test_validate_cmd_with_invalid_doc(tmp_path: pathlib.Path, cli_runner: CliRunner):
    beanhub_dir = tmp_path / ".beanhub"
    beanhub_dir.mkdir()
    form_doc = beanhub_dir / "forms.yaml"
    form_doc.write_text("{}")

    cli_runner.mix_stderr = False
    with switch_cwd(tmp_path):
        result = cli_runner.invoke(cli, ["form", "validate"])
    assert result.exit_code == -1
    assert "Invalid form document with errors" in result.stderr
