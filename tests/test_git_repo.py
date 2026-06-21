import pathlib

import pytest

from beanhub_cli.auth import ensure_auth_config
from beanhub_cli.config import AccessToken
from beanhub_cli.config import Config
from beanhub_cli.config import save_config
from beanhub_cli.git_repo import find_git_root
from beanhub_cli.git_repo import get_remote_url
from beanhub_cli.git_repo import parse_beanhub_repo_from_remote
from beanhub_cli.git_repo import resolve_repo_from_git
from tests.helper import switch_cwd


def _write_git_repo(
    repo_root: pathlib.Path,
    remote_url: str,
    *,
    git_dir: pathlib.Path | None = None,
) -> None:
    if git_dir is None:
        git_dir = repo_root / ".git"
        git_dir.mkdir(parents=True)
    else:
        git_dir.mkdir(parents=True)
        (repo_root / ".git").write_text(f"gitdir: {git_dir}\n")

    (git_dir / "config").write_text(
        f'[remote "origin"]\n\turl = {remote_url}\n',
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("remote_url", "expected"),
    [
        (
            "https://app.beanhub.io/repos/alice/my-book.git",
            ("alice", "my-book"),
        ),
        (
            "https://alice:token@app.beanhub.io/repos/alice/my-book.git",
            ("alice", "my-book"),
        ),
        (
            "https://app.beanhub.io/repos/alice/my-book",
            ("alice", "my-book"),
        ),
        (
            "git@app.beanhub.io:repos/alice/my-book.git",
            ("alice", "my-book"),
        ),
        (
            "git@app.beanhub.io:alice/my-book.git",
            ("alice", "my-book"),
        ),
        ("https://github.com/alice/my-book.git", None),
        ("git@github.com:LaunchPlatform/beanhub-cli.git", None),
    ],
)
def test_parse_beanhub_repo_from_remote(
    remote_url: str, expected: tuple[str, str] | None
):
    assert parse_beanhub_repo_from_remote(remote_url) == expected


def test_find_git_root_walks_up_parent_directories(tmp_path: pathlib.Path):
    repo_root = tmp_path / "repo"
    nested_dir = repo_root / "books" / "2024"
    nested_dir.mkdir(parents=True)
    _write_git_repo(repo_root, "https://app.beanhub.io/repos/alice/my-book.git")

    with switch_cwd(nested_dir):
        assert find_git_root() == repo_root.resolve()


def test_resolve_repo_from_git_uses_origin_remote(tmp_path: pathlib.Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_git_repo(
        repo_root,
        "https://app.beanhub.io/repos/alice/my-book.git",
    )

    with switch_cwd(repo_root):
        assert resolve_repo_from_git() == "alice/my-book"


def test_resolve_repo_from_git_supports_gitdir_file(tmp_path: pathlib.Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = tmp_path / "actual-git-dir"
    _write_git_repo(
        repo_root,
        "https://app.beanhub.io/repos/alice/my-book.git",
        git_dir=git_dir,
    )

    with switch_cwd(repo_root):
        assert resolve_repo_from_git() == "alice/my-book"


def test_get_remote_url_reads_origin(tmp_path: pathlib.Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text(
        '[remote "origin"]\n\turl = "https://app.beanhub.io/repos/alice/my-book.git"\n',
        encoding="utf-8",
    )

    assert get_remote_url(git_dir) == "https://app.beanhub.io/repos/alice/my-book.git"


def test_resolve_repo_from_git_returns_none_for_non_beanhub_remote(
    tmp_path: pathlib.Path,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_git_repo(repo_root, "https://github.com/alice/my-book.git")

    with switch_cwd(repo_root):
        assert resolve_repo_from_git() is None


def test_ensure_auth_config_uses_git_remote_when_active(
    tmp_path: pathlib.Path,
    mock_home: pathlib.Path,
    httpx_mock,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_git_repo(
        repo_root,
        "https://app.beanhub.io/repos/alice/my-book.git",
    )
    save_config(Config(access_token=AccessToken(token="test-token")))
    httpx_mock.add_response(
        url="https://api.beanhub.io/v1/repositories",
        method="GET",
        status_code=200,
        json=dict(
            repositories=[
                dict(
                    username="alice",
                    name="my-book",
                    type="GIT",
                    public=False,
                    active=True,
                )
            ]
        ),
        match_headers={"access-token": "test-token"},
    )

    with switch_cwd(repo_root):
        config = ensure_auth_config(api_base_url="https://api.beanhub.io", repo=None)

    assert config.username == "alice"
    assert config.repo == "my-book"


def test_ensure_auth_config_falls_back_to_single_active_repo(
    tmp_path: pathlib.Path,
    mock_home: pathlib.Path,
    httpx_mock,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_git_repo(
        repo_root,
        "git@github.com:LaunchPlatform/beanhub-cli.git",
    )
    save_config(Config(access_token=AccessToken(token="test-token")))
    httpx_mock.add_response(
        url="https://api.beanhub.io/v1/repositories",
        method="GET",
        status_code=200,
        json=dict(
            repositories=[
                dict(
                    username="alice",
                    name="my-book",
                    type="GIT",
                    public=False,
                    active=True,
                )
            ]
        ),
        match_headers={"access-token": "test-token"},
    )

    with switch_cwd(repo_root):
        config = ensure_auth_config(api_base_url="https://api.beanhub.io", repo=None)

    assert config.username == "alice"
    assert config.repo == "my-book"
