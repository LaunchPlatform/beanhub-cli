import pathlib
import platform
import secrets
import uuid

import httpx
import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock
from pytest_mock import MockFixture

from beanhub_cli.config import Config
from beanhub_cli.config import load_config
from beanhub_cli.main import cli


@pytest.mark.parametrize("open_browser_success", [True, False])
def test_login(
    mock_home: pathlib.Path,
    cli_runner: CliRunner,
    httpx_mock: HTTPXMock,
    mocker: MockFixture,
    open_browser_success: bool,
):
    open_browser = mocker.patch("webbrowser.open")
    open_browser.return_value = open_browser_success
    mock_token = secrets.token_urlsafe(8)
    secret_token = secrets.token_urlsafe(8)
    session_id = uuid.uuid4()
    auth_url = (
        f"https://app.beanhub.io/access-tokens/create?auth_session_id={session_id}"
    )
    httpx_mock.add_response(
        url="https://api.beanhub.io/v1/auth/sessions",
        method="POST",
        status_code=201,
        json=dict(
            id=str(session_id),
            code="ABCD-1234",
            auth_url=auth_url,
            secret_token=secret_token,
        ),
        match_json=dict(
            hostname=platform.node(),
        ),
    )
    httpx_mock.add_response(
        url=httpx.URL(
            f"https://api.beanhub.io/v1/auth/sessions/{session_id}/poll",
            params=dict(secret_token=secret_token),
        ),
        method="GET",
        status_code=202,
        json=dict(
            code="try_again",
            message="Try again later",
        ),
    )
    httpx_mock.add_response(
        url=httpx.URL(
            f"https://api.beanhub.io/v1/auth/sessions/{session_id}/poll",
            params=dict(secret_token=secret_token),
        ),
        method="GET",
        status_code=200,
        json=dict(
            token=mock_token,
        ),
    )

    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["login"])
    assert result.exit_code == 0
    open_browser.assert_called_once_with(auth_url, new=2)

    config = load_config()
    assert config.access_token.token == mock_token
    assert config.repo is None


def test_already_login(
    cli_runner: CliRunner,
    mock_config: Config,
):
    _ = mock_config
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["login"])
    assert result.exit_code == -1
    assert "Already logged in" in result.stderr
