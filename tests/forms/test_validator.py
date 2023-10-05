import pathlib

import pytest

from beanhub_cli.forms.validator import validate_doc


def test_file_does_not_exist(tmp_path: pathlib.Path):
    doc_file = tmp_path / "does-not-exists.yaml"
    with pytest.raises(ValueError) as error:
        validate_doc(doc_file)
    assert error.value.args[0] == f"Form document at {doc_file} does not exist"
