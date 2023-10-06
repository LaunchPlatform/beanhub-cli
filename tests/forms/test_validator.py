import pathlib

import pytest
import yaml
from pydantic import ValidationError

from beanhub_cli.forms.validator import validate_doc


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
