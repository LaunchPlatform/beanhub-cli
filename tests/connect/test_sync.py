import pathlib
import uuid

from click.testing import CliRunner
from pytest_httpx import HTTPXMock

from beanhub_cli.config import Config
from beanhub_cli.main import cli


def test_sync(
    cli_runner: CliRunner,
    mock_config: Config,
    httpx_mock: HTTPXMock,
):
    batch_id = uuid.uuid4()
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/sync_batches",
        method="POST",
        status_code=201,
        json=dict(
            id=str(batch_id),
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/sync_batches/{batch_id}",
        method="GET",
        status_code=200,
        json=dict(
            id=str(batch_id),
            syncs=[
                dict(
                    id="SYNC0",
                    state="PROCESSING",
                    item=dict(
                        id="MOCK_ITEM0",
                        institution_name="Chase",
                    ),
                ),
                dict(
                    id="SYNC1",
                    state="PROCESSING",
                    item=dict(
                        id="MOCK_ITEM1",
                        institution_name="Chase",
                    ),
                ),
            ],
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/sync_batches/{batch_id}",
        method="GET",
        status_code=200,
        json=dict(
            id=str(batch_id),
            syncs=[
                dict(
                    id="SYNC0",
                    state="IMPORT_COMPLETE_NO_CHANGES",
                    item=dict(
                        id="MOCK_ITEM0",
                        institution_name="Chase",
                    ),
                ),
                dict(
                    id="SYNC1",
                    state="IMPORT_COMPLETE",
                    item=dict(
                        id="MOCK_ITEM1",
                        institution_name="Chase",
                    ),
                ),
            ],
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["connect", "sync"])
    assert result.exit_code == 0


def test_sync_not_logged_in(
    cli_runner: CliRunner,
    mock_home: pathlib.Path,
    httpx_mock: HTTPXMock,
):
    _ = httpx_mock
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["connect", "sync"])
    assert result.exit_code == -1
    assert "You need to login into your BeanHub account" in result.stderr
