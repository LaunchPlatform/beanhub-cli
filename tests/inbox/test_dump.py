import json
import pathlib
import uuid

import pytest
from beanhub_inbox.data_types import ArchiveInboxAction
from beanhub_inbox.data_types import InboxConfig
from beanhub_inbox.data_types import InboxDoc
from beanhub_inbox.data_types import InboxEmail
from click.testing import CliRunner
from nacl.encoding import URLSafeBase64Encoder
from nacl.public import PrivateKey
from nacl.public import SealedBox
from pytest_httpx import HTTPXMock
from pytest_mock import MockFixture

from ..factories import InboxEmailFactory
from ..helper import switch_cwd
from beanhub_cli.config import Config
from beanhub_cli.inbox.main import compute_missing_emails
from beanhub_cli.main import cli


@pytest.fixture
def mock_private_key(mocker: MockFixture) -> PrivateKey:
    key = PrivateKey.generate()
    with mocker.patch("nacl.public.PrivateKey.generate", return_value=key):
        yield key


@pytest.mark.parametrize(
    "inbox_doc, inbox_emails, existing_files, expected",
    [
        (
            InboxDoc(),
            [],
            [],
            [],
        ),
        (
            InboxDoc(
                inbox=[
                    InboxConfig(
                        action=ArchiveInboxAction(
                            output_file="inbox-data/default/{{ id }}.eml"
                        )
                    )
                ]
            ),
            [
                InboxEmailFactory(id="email0"),
                InboxEmailFactory(id="email1"),
                InboxEmailFactory(id="email2"),
            ],
            [
                "inbox-data/default/email1.eml",
            ],
            [
                ("email0", "inbox-data/default/email0.eml"),
                ("email2", "inbox-data/default/email2.eml"),
            ],
        ),
    ],
)
def test_compute_missing_emails(
    tmp_path: pathlib.Path,
    inbox_doc: InboxDoc,
    inbox_emails: list[InboxEmail],
    existing_files: list[str],
    expected: list[tuple[InboxEmail, pathlib.Path]],
):
    for existing_file in existing_files:
        existing_file_path = tmp_path / existing_file
        existing_file_path.parent.mkdir(parents=True, exist_ok=True)
        existing_file_path.write_text("")
    assert (
        list(
            map(
                lambda item: (item[0].id, str(item[1])),
                compute_missing_emails(
                    inbox_doc=inbox_doc,
                    inbox_emails=inbox_emails,
                    workdir_path=tmp_path,
                ),
            )
        )
        == expected
    )


def test_dump(
    tmp_path: pathlib.Path,
    cli_runner: CliRunner,
    mock_config: Config,
    httpx_mock: HTTPXMock,
    mock_private_key: PrivateKey,
    mocker: MockFixture,
):
    mock_decrypt_file = mocker.patch("beanhub_cli.encryption.decrypt_file")
    mock_extract_inbox_tar = mocker.patch("beanhub_cli.file_io.extract_inbox_tar")

    emails = [
        InboxEmailFactory(id="email0"),
        InboxEmailFactory(id="email1"),
        InboxEmailFactory(id="email2"),
        InboxEmailFactory(id="email3"),
        InboxEmailFactory(id="email4"),
    ]
    inbox_doc = InboxDoc(
        inbox=[
            InboxConfig(
                action=ArchiveInboxAction(output_file="inbox-data/default/{{ id }}.eml")
            )
        ]
    )
    inbox_doc_path = tmp_path / ".beanhub" / "inbox.yaml"
    inbox_doc_path.parent.mkdir(exist_ok=True, parents=True)
    inbox_doc_path.write_text(inbox_doc.model_dump_json())
    existing_files = [
        emails[1].id,
    ]
    for existing_file in existing_files:
        existing_file_path = tmp_path / existing_file
        existing_file_path.parent.mkdir(parents=True, exist_ok=True)
        existing_file_path.write_text("")

    dump_id = uuid.uuid4()
    public_key = mock_private_key.public_key.encode(URLSafeBase64Encoder).decode(
        "ascii"
    )
    mock_download_url = "https://example.com/download"
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
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/inbox/emails",
        method="GET",
        status_code=200,
        json=dict(
            emails=[
                emails[0].model_dump(mode="json"),
                emails[2].model_dump(mode="json"),
                emails[3].model_dump(mode="json"),
            ],
            cursor="MOCK_CURSOR0",
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/inbox/emails?cursor=MOCK_CURSOR0",
        method="GET",
        status_code=200,
        json=dict(
            emails=[
                emails[4].model_dump(mode="json"),
            ],
            cursor="MOCK_CURSOR1",
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/inbox/emails?cursor=MOCK_CURSOR1",
        method="GET",
        status_code=200,
        json=dict(
            emails=[],
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/inbox/dumps",
        method="POST",
        status_code=201,
        json=dict(
            id=str(dump_id),
        ),
        match_json=dict(
            public_key=public_key,
            email_ids=[
                emails[0].id,
                emails[2].id,
                emails[3].id,
                emails[4].id,
            ],
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/inbox/dumps/{dump_id}",
        method="GET",
        status_code=200,
        json=dict(
            id=str(dump_id),
            state="PROCESSING",
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/inbox/dumps/{dump_id}",
        method="GET",
        status_code=200,
        json=dict(
            id=str(dump_id),
            state="COMPLETE",
            download_url=mock_download_url,
            encryption_key=encryption_key,
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )
    httpx_mock.add_response(
        url=mock_download_url,
        method="GET",
        status_code=200,
        content=b"MOCK_FILE_CONTENT",
    )

    cli_runner.mix_stderr = False
    with switch_cwd(tmp_path):
        result = cli_runner.invoke(
            cli,
            [
                "inbox",
                "dump",
                "-w",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
    mock_decrypt_file.assert_called_once()
    mock_extract_inbox_tar.assert_called_once()


def test_dump_without_emails(
    cli_runner: CliRunner,
    mock_config: Config,
    httpx_mock: HTTPXMock,
    mock_private_key: PrivateKey,
):
    httpx_mock.add_response(
        url=f"https://api.beanhub.io/v1/repos/{mock_config.repo.default}/inbox/emails",
        method="GET",
        status_code=200,
        json=dict(
            emails=[],
        ),
        match_headers={"access-token": mock_config.access_token.token},
    )

    cli_runner.mix_stderr = False
    result = cli_runner.invoke(
        cli,
        [
            "inbox",
            "dump",
        ],
    )
    assert result.exit_code == 0
    assert "No missing emails found, no need to update" in result.stderr
