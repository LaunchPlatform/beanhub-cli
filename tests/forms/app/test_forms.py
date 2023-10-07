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
