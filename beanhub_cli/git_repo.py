import configparser
import pathlib
import re

BEANHUB_HTTPS_REMOTE_PATTERN = re.compile(
    r"beanhub\.io/(?:.*?/)?repos/(?P<username>[^/]+)/(?P<repo_name>[^/.]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
BEANHUB_SSH_REMOTE_PATTERN = re.compile(
    r"^git@[^:]*beanhub[^:]*:(?:repos/)?(?P<username>[^/]+)/(?P<repo_name>[^/.]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def find_git_root(start_path: pathlib.Path | None = None) -> pathlib.Path | None:
    path = (start_path or pathlib.Path.cwd()).resolve()
    for current in [path, *path.parents]:
        if (current / ".git").exists():
            return current
    return None


def _resolve_git_dir(repo_root: pathlib.Path) -> pathlib.Path | None:
    git_path = repo_root / ".git"
    if git_path.is_dir():
        return git_path
    if git_path.is_file():
        gitdir_line = git_path.read_text().splitlines()[0]
        if gitdir_line.startswith("gitdir: "):
            git_dir = pathlib.Path(gitdir_line.removeprefix("gitdir: ").strip())
            if not git_dir.is_absolute():
                git_dir = (repo_root / git_dir).resolve()
            return git_dir
    return None


def get_remote_url(git_dir: pathlib.Path, remote_name: str = "origin") -> str | None:
    config_path = git_dir / "config"
    if not config_path.is_file():
        return None

    parser = configparser.ConfigParser()
    parser.read(config_path)
    section = f'remote "{remote_name}"'
    if section not in parser:
        return None

    url = parser[section].get("url")
    if url is None:
        return None
    return url.strip().strip('"').strip("'")


def parse_beanhub_repo_from_remote(url: str) -> tuple[str, str] | None:
    url = url.strip()
    ssh_match = BEANHUB_SSH_REMOTE_PATTERN.match(url)
    if ssh_match is not None:
        return ssh_match.group("username"), ssh_match.group("repo_name")

    https_match = BEANHUB_HTTPS_REMOTE_PATTERN.search(url)
    if https_match is not None:
        return https_match.group("username"), https_match.group("repo_name")
    return None


def resolve_repo_from_git(start_path: pathlib.Path | None = None) -> str | None:
    git_root = find_git_root(start_path)
    if git_root is None:
        return None

    git_dir = _resolve_git_dir(git_root)
    if git_dir is None:
        return None

    remote_url = get_remote_url(git_dir)
    if remote_url is None:
        return None

    parsed = parse_beanhub_repo_from_remote(remote_url)
    if parsed is None:
        return None
    username, repo_name = parsed
    return f"{username}/{repo_name}"
