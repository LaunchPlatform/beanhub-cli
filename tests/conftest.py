import pathlib
import secrets

import pytest
from click.testing import CliRunner
from pytest_mock import MockFixture

from beanhub_cli.config import AccessToken
from beanhub_cli.config import Config
from beanhub_cli.config import Repository
from beanhub_cli.config import save_config


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_home(tmp_path: pathlib.Path, mocker: MockFixture) -> pathlib.Path:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    with mocker.patch("pathlib.Path.home", return_value=home_dir):
        yield home_dir


@pytest.fixture
def config_username() -> str | None:
    return "MOCK_USERNAME"


@pytest.fixture
def config_repo_name() -> str | None:
    return "MOCK_REPO"


@pytest.fixture
def mock_config(
    mock_home: pathlib.Path, config_username: str | None, config_repo_name: str | None
) -> Config:
    _ = mock_home
    token = secrets.token_urlsafe(8)
    config = Config(access_token=AccessToken(token=token))
    if config_username is not None and config_repo_name is not None:
        config.repo = Repository(default=f"{config_username}/{config_repo_name}")
    save_config(config)
    return config
