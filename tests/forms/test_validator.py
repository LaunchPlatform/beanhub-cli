import pathlib

import pytest
import yaml
from beanhub_forms.data_types.form import FormDoc
from click.testing import CliRunner
from pydantic import ValidationError

from ..helper import switch_cwd
from beanhub_cli.forms.validator import format_loc
from beanhub_cli.forms.validator import merge_index_loc
from beanhub_cli.forms.validator import validate_doc
from beanhub_cli.main import cli


@pytest.mark.parametrize(
    "loc, expected",
    [
        (("",), ""),
        (
            ("forms", 0, "fields", 0, "StrFormField", "type"),
            "forms[0].fields[0].StrFormField.type",
        ),
    ],
)
def test_format_loc(loc: tuple[str, ...], expected: str):
    assert format_loc(loc) == expected


@pytest.mark.parametrize(
    "loc, expected",
    [
        (("",), ("",)),
        (("a", "b", "c"), ("a", "b", "c")),
        ((0,), ("[0]",)),
        ((0, "child"), ("[0]", "child")),
        ((1, 2, 3), ("[1][2][3]",)),
        (
            ("root", 1, "child"),
            (
                "root[1]",
                "child",
            ),
        ),
        (
            ("root", "child", 0),
            (
                "root",
                "child[0]",
            ),
        ),
    ],
)
def test_merge_index_loc(loc: tuple[str, ...], expected: tuple[str, ...]):
    assert merge_index_loc(loc) == expected


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
                },
                {
                    "type": "missing",
                    "loc": ("forms", 0, "fields"),
                    "msg": "Field required",
                    "input": {},
                },
                {
                    "type": "missing",
                    "loc": ("forms", 0, "operations"),
                    "msg": "Field required",
                    "input": {},
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

    def del_url(d):
        del d["url"]
        return d

    assert list(map(del_url, exc.value.errors())) == expected_errors


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
    assert "Form document is valid" in result.stdout


@pytest.mark.parametrize(
    "form_doc, expected_error",
    [
        ("", "Invalid form document with errors"),
        ("{}", "Invalid form document with errors"),
        ('"', "Invalid form document with YAML errors"),
    ],
)
def test_validate_cmd_with_invalid_doc(
    tmp_path: pathlib.Path, cli_runner: CliRunner, form_doc: str, expected_error: str
):
    beanhub_dir = tmp_path / ".beanhub"
    beanhub_dir.mkdir()
    form_doc_file = beanhub_dir / "forms.yaml"
    form_doc_file.write_text(form_doc)

    cli_runner.mix_stderr = False
    with switch_cwd(tmp_path):
        result = cli_runner.invoke(cli, ["form", "validate"])
    assert result.exit_code == -1
    assert expected_error in result.stderr
