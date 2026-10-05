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
    assert "bh logout" in result.stderr


def _mock_revoke(httpx_mock: HTTPXMock, token: str, status_code: int):
    httpx_mock.add_response(
        url="https://api.beanhub.io/v1/auth/token",
        method="DELETE",
        status_code=status_code,
        match_headers={"access-token": token},
    )


def test_logout_keeps_other_settings(
    cli_runner: CliRunner,
    httpx_mock: HTTPXMock,
    mock_config: Config,
):
    token = mock_config.access_token.token
    _mock_revoke(httpx_mock, token, 204)
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["logout"])
    assert result.exit_code == 0
    assert "Revoked the access token" in result.stderr

    config = load_config()
    assert config is not None
    assert config.access_token is None
    assert config.repo is not None
    assert config.repo.default == mock_config.repo.default
    saved = pathlib.Path.home().joinpath(".beanhub", "config.toml").read_text()
    assert token not in saved


@pytest.mark.parametrize("config_username", [None])
@pytest.mark.parametrize("config_repo_name", [None])
def test_logout_deletes_config_when_it_only_holds_the_token(
    cli_runner: CliRunner,
    httpx_mock: HTTPXMock,
    mock_home: pathlib.Path,
    mock_config: Config,
):
    _mock_revoke(httpx_mock, mock_config.access_token.token, 204)
    config_path = mock_home / ".beanhub" / "config.toml"
    assert config_path.exists()
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["logout"])
    assert result.exit_code == 0
    assert not config_path.exists()
    assert load_config() is None


@pytest.mark.parametrize(
    "status_code, message",
    [
        (401, "invalid"),
        (404, "stops working"),
    ],
)
def test_logout_drops_local_token_when_revoke_cannot_succeed(
    cli_runner: CliRunner,
    httpx_mock: HTTPXMock,
    mock_config: Config,
    status_code: int,
    message: str,
):
    _mock_revoke(httpx_mock, mock_config.access_token.token, status_code)
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["logout"])
    assert result.exit_code == 0
    assert message in result.stderr
    config = load_config()
    assert config.access_token is None
    assert config.repo.default == mock_config.repo.default


def test_logout_keeps_login_when_revoke_fails(
    cli_runner: CliRunner,
    httpx_mock: HTTPXMock,
    mock_config: Config,
):
    token = mock_config.access_token.token
    _mock_revoke(httpx_mock, token, 500)
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["logout"])
    assert result.exit_code == -1
    assert "still logged in" in result.stderr
    assert load_config().access_token.token == token


def test_logout_keeps_login_when_bean_hub_is_unreachable(
    cli_runner: CliRunner,
    httpx_mock: HTTPXMock,
    mock_config: Config,
):
    token = mock_config.access_token.token
    httpx_mock.add_exception(httpx.ConnectError("offline"))
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["logout"])
    assert result.exit_code == -1
    assert "still logged in" in result.stderr
    assert load_config().access_token.token == token


def test_logout_when_not_logged_in(
    cli_runner: CliRunner,
    httpx_mock: HTTPXMock,
    mock_home: pathlib.Path,
):
    _ = mock_home
    _ = httpx_mock
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["logout"])
    assert result.exit_code == 0
    assert "Not logged in" in result.stderr
    assert load_config() is None
