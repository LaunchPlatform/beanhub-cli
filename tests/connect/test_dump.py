import json
import uuid

import pytest
from click.testing import CliRunner
from nacl.encoding import URLSafeBase64Encoder
from nacl.public import PrivateKey
from nacl.public import SealedBox
from pytest_httpx import HTTPXMock
from pytest_mock import MockFixture

from beanhub_cli.config import Config
from beanhub_cli.main import cli


@pytest.fixture
def mock_private_key(mocker: MockFixture) -> PrivateKey:
    key = PrivateKey.generate()
    with mocker.patch("nacl.public.PrivateKey.generate", return_value=key):
        yield key


@pytest.mark.parametrize("output_accounts", [False, True])
def test_dump(
    cli_runner: CliRunner,
    mock_config: Config,
    httpx_mock: HTTPXMock,
    mock_private_key: PrivateKey,
    mocker: MockFixture,
    output_accounts: bool,
):
    mock_decrypt_file = mocker.patch("beanhub_cli.encryption.decrypt_file")
    mock_extract_tar = mocker.patch("beanhub_cli.file_io.extract_tar")

    dump_id = uuid.uuid4()
    public_key = mock_private_key.public_key.encode(URLSafeBase64Encoder).decode(
        "ascii"
    )
    mock_download_url = "https://example.com/download"
    mock_accounts_download_url = "https://example.com/download-accounts"
    box = SealedBox(mock_private_key)
    encryption_key = box.encrypt(
        json.dumps(
            dict(
                key=URLSafeBase64Encoder.encode(b"MOCK_KEY").decode("ascii"),
                iv=URLSafeBase64Encoder.encode(b"MOCK_IV").decode("ascii"),
            )
        ).encode("ascii"),
        encoder=URLSafeBase64Encoder,
    ).decode("ascii")

    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/dumps",
        method="POST",
        status_code=201,
        json=dict(
            id=str(dump_id),
        ),
        match_json=dict(
            public_key=public_key,
            output_accounts=output_accounts,
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/dumps/{dump_id}",
        method="GET",
        status_code=200,
        json=dict(
            id=str(dump_id),
            state="PROCESSING",
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/connect/dumps/{dump_id}",
        method="GET",
        status_code=200,
        json=dict(
            id=str(dump_id),
            state="COMPLETE",
            download_url=mock_download_url,
            encryption_key=encryption_key,
            **(
                dict(accounts_download_url=mock_accounts_download_url)
                if output_accounts
                else {}
            ),
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=mock_download_url,
        method="GET",
        status_code=200,
        content=b"MOCK_FILE_CONTENT",
    )
    if output_accounts:
        httpx_mock.add_response(
            url=mock_accounts_download_url,
            method="GET",
            status_code=200,
            content=b"MOCK_ACCOUNTS_FILE_CONTENT",
        )

    cli_runner.mix_stderr = False
    result = cli_runner.invoke(
        cli,
        [
            "connect",
            "dump",
            *((f"--output-accounts=.",) if output_accounts else tuple()),
        ],
    )
    assert result.exit_code == 0
    if not output_accounts:
        mock_decrypt_file.assert_called_once()
    else:
        assert mock_decrypt_file.call_count == 2
    mock_extract_tar.assert_called_once()
