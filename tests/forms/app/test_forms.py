import pathlib
import textwrap
import typing

import pytest
from starlette.testclient import TestClient

from beanhub_cli.forms.app.settings import Settings


@pytest.fixture
def make_form_doc(tmp_path: pathlib.Path) -> pathlib.Path:
    def _make_form_doc(content: str) -> pathlib.Path:
        form_doc = tmp_path / ".beanhub" / "forms.yaml"
        form_doc.parent.mkdir()
        form_doc.write_text(content)
        return tmp_path

    return _make_form_doc


def test_form_list(
    make_form_doc: typing.Callable,
    settings: Settings,
    client: TestClient,
):
    settings.BEANCOUNT_DIR = make_form_doc(
        textwrap.dedent(
            """\
    forms:
    - name: form0
      fields: []
      operations: []
    - name: form1
      fields: []
      operations: []
    """
        )
    )
    resp = client.get("/")
    assert resp.status_code == 200
    assert "form0" in resp.text
    assert "form1" in resp.text
    assert "form2" not in resp.text


def test_form_list_without_doc(
    settings: Settings,
    client: TestClient,
):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "No form definitions found" in resp.text


@pytest.mark.parametrize(
    "form_doc",
    [
        '"bad-yaml',
        textwrap.dedent(
            """\
    forms:
    - name: "foo
    """
        ),
        textwrap.dedent(
            """\
    forms:
    - fields: []
      operations: []
    """
        ),
    ],
)
def test_form_list_with_bad_doc(
    make_form_doc: typing.Callable,
    settings: Settings,
    client: TestClient,
    form_doc: str,
):
    settings.BEANCOUNT_DIR = make_form_doc(form_doc)
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "http://testserver/errors"


@pytest.mark.parametrize(
    "form_doc, expected_error",
    [
        ('"bad-yaml', "while scanning a quoted scalar"),
        (
            textwrap.dedent(
                """\
    forms:
    - name: "foo
      fields:
      - name: "myfield"
        type: date
      
    """
            ),
            "while parsing a block mapping",
        ),
        (
            textwrap.dedent(
                """\
    forms:
    - fields: []
      operations: []
    """
            ),
            "Field required",
        ),
    ],
)
def test_errors(
    make_form_doc: typing.Callable,
    settings: Settings,
    client: TestClient,
    form_doc: str,
    expected_error: str,
):
    settings.BEANCOUNT_DIR = make_form_doc(form_doc)
    resp = client.get("/errors")
    assert resp.status_code == 200
    assert expected_error in resp.text
