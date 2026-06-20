import pathlib
import uuid

import pytest
from click.testing import CliRunner
from pytest_httpx import HTTPXMock
from pytest_mock import MockFixture

from beanhub_cli.config import Config
from beanhub_cli.main import cli


@pytest.fixture(autouse=True)
def mock_sleep(mocker: MockFixture):
    mocker.patch("beanhub_cli.connect.main.time.sleep")


def _sync_batch_payload(
    batch_id: uuid.UUID,
    *,
    import_and_commit: bool = False,
    state: str = "SYNCING",
    syncs: list[dict],
    all_syncs_succeeded: bool | None = None,
    error_message: str | None = None,
) -> dict:
    payload = dict(
        id=str(batch_id),
        import_and_commit=import_and_commit,
        state=state,
        syncs=syncs,
    )
    if all_syncs_succeeded is not None:
        payload["all_syncs_succeeded"] = all_syncs_succeeded
    if error_message is not None:
        payload["error_message"] = error_message
    return payload


def _mock_list_repo(
    httpx_mock: HTTPXMock,
    mock_config: Config,
    *,
    repo_type: str,
):
    username, repo_name = mock_config.repo.default.split("/", 1)
    httpx_mock.add_response(
        url="https://api.beanhub.io/v1/repositories",
        method="GET",
        status_code=200,
        json=dict(
            repositories=[
                dict(
                    username=username,
                    name=repo_name,
                    type=repo_type,
                    public=False,
                    active=True,
                )
            ]
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )


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
        json=_sync_batch_payload(
            batch_id,
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
        json=_sync_batch_payload(
            batch_id,
            state="SYNC_COMPLETE",
            all_syncs_succeeded=True,
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


def test_sync_with_skipped_state(
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
        json=_sync_batch_payload(
            batch_id,
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
        json=_sync_batch_payload(
            batch_id,
            state="SYNC_COMPLETE",
            all_syncs_succeeded=False,
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
                    state="SKIPPED",
                    item=dict(
                        id="MOCK_ITEM1",
                        institution_name="Chase",
                    ),
                    error_message='Your login session has expired, please use the "Update" button to login to your bank account with Plaid again',
                ),
            ],
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["connect", "sync"])
    assert result.exit_code == 0
    assert "Your login session has expired" in result.stdout.replace("\n", "")


def test_sync_with_import_and_commit(
    cli_runner: CliRunner,
    mock_config: Config,
    httpx_mock: HTTPXMock,
):
    batch_id = uuid.uuid4()
    _mock_list_repo(httpx_mock, mock_config, repo_type="GIT")
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/sync_batches",
        method="POST",
        status_code=201,
        json=dict(
            id=str(batch_id),
        ),
        match_headers={"access-token": mock_config.access_token.token},
        match_json={"import_and_commit": True},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/sync_batches/{batch_id}",
        method="GET",
        status_code=200,
        json=_sync_batch_payload(
            batch_id,
            import_and_commit=True,
            state="SYNCING",
            syncs=[
                dict(
                    id="SYNC0",
                    state="PROCESSING",
                    item=dict(
                        id="MOCK_ITEM0",
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
        json=_sync_batch_payload(
            batch_id,
            import_and_commit=True,
            state="IMPORTING",
            syncs=[
                dict(
                    id="SYNC0",
                    state="SYNC_COMPLETE",
                    item=dict(
                        id="MOCK_ITEM0",
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
        json=_sync_batch_payload(
            batch_id,
            import_and_commit=True,
            state="IMPORT_COMPLETE",
            all_syncs_succeeded=True,
            syncs=[
                dict(
                    id="SYNC0",
                    state="SYNC_COMPLETE",
                    item=dict(
                        id="MOCK_ITEM0",
                        institution_name="Chase",
                    ),
                ),
            ],
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["connect", "sync", "--import-and-commit"])
    assert result.exit_code == 0
    output = result.stdout.replace("\n", "") + result.stderr.replace("\n", "")
    assert "Batch import and commit finished" in output


def test_sync_with_import_and_commit_failed(
    cli_runner: CliRunner,
    mock_config: Config,
    httpx_mock: HTTPXMock,
):
    batch_id = uuid.uuid4()
    _mock_list_repo(httpx_mock, mock_config, repo_type="GIT")
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/sync_batches",
        method="POST",
        status_code=201,
        json=dict(
            id=str(batch_id),
        ),
        match_headers={"access-token": mock_config.access_token.token},
        match_json={"import_and_commit": True},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/sync_batches/{batch_id}",
        method="GET",
        status_code=200,
        json=_sync_batch_payload(
            batch_id,
            import_and_commit=True,
            state="IMPORT_FAILED",
            all_syncs_succeeded=True,
            error_message=(
                "Unexpected error while processing import, please contract support for help"
            ),
            syncs=[
                dict(
                    id="SYNC0",
                    state="IMPORT_FAILED",
                    error_message=(
                        "Unexpected error while processing import, please contract support for help"
                    ),
                    item=dict(
                        id="MOCK_ITEM0",
                        institution_name="Chase",
                    ),
                ),
                dict(
                    id="SYNC1",
                    state="IMPORT_FAILED",
                    error_message=(
                        "Unexpected error while processing import, please contract support for help"
                    ),
                    item=dict(
                        id="MOCK_ITEM1",
                        institution_name="Wells Fargo",
                    ),
                ),
            ],
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["connect", "sync", "--import-and-commit"])
    assert result.exit_code == -1
    output = result.stdout.replace("\n", "") + result.stderr.replace("\n", "")
    assert "Batch import and commit failed with error" in output
    assert "Unexpected error while processing import" in output


def test_sync_with_import_and_commit_connect_only(
    cli_runner: CliRunner,
    mock_config: Config,
    httpx_mock: HTTPXMock,
):
    _mock_list_repo(httpx_mock, mock_config, repo_type="CONNECT")
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["connect", "sync", "--import-and-commit"])
    assert result.exit_code == -1
    output = result.stdout.replace("\n", "") + result.stderr.replace("\n", "")
    assert "syncing transactions and exporting data" in output


def test_sync_with_import_and_commit_rejected_by_api(
    cli_runner: CliRunner,
    mock_config: Config,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        url="https://api.beanhub.io/v1/repositories",
        method="GET",
        status_code=200,
        json=dict(repositories=[]),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/sync_batches",
        method="POST",
        status_code=422,
        json=dict(
            error=(
                "Import and commit is only available for Git repositories. "
                "Connect repositories only support syncing transactions and "
                "exporting data."
            ),
        ),
        match_headers={"access-token": mock_config.access_token.token},
        match_json={"import_and_commit": True},
    )
    cli_runner.mix_stderr = False
    result = cli_runner.invoke(cli, ["connect", "sync", "--import-and-commit"])
    assert result.exit_code == -1
    output = result.stdout.replace("\n", "") + result.stderr.replace("\n", "")
    assert "syncing transactions and exporting data" in output


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
