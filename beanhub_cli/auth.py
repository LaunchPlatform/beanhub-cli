import dataclasses
import logging
import sys
import typing

from .config import load_config
from .git_repo import resolve_repo_from_git
from .http_client import make_auth_client

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class AuthConfig:
    token: str
    username: str
    repo: str


def parse_repo(repo: str | None) -> typing.Tuple[str | None, str | None]:
    if repo is None:
        return None, None
    return tuple(repo.split("/", 1))


# TODO: maybe extract this part to a shared env for connect command?
def ensure_auth_config(api_base_url: str, repo: str | None) -> AuthConfig:
    config = load_config()
    if config is None or config.access_token is None:
        logger.error(
            'You need to login into your BeanHub account with "bh login" command first'
        )
        sys.exit(-1)
    if repo is None and (config.repo is None or config.repo.default is None):
        git_repo = resolve_repo_from_git()
        if git_repo is not None:
            logger.info(
                "Determined repo automatically from git remote: %s",
                git_repo,
            )
            username, repo_name = parse_repo(git_repo)
            return AuthConfig(
                token=config.access_token.token,
                username=username,
                repo=repo_name,
            )

        logger.info(
            "No repo provided, try to determine which repo to use automatically ..."
        )

        from .internal_api.api.repo import list_repo

        with make_auth_client(
            base_url=api_base_url, token=config.access_token.token
        ) as client:
            client.raise_on_unexpected_status = True
            resp = list_repo.sync(client=client)
            active_repos = list(filter(lambda repo: repo.active, resp.repositories))
            if len(active_repos) == 1:
                active_repo = active_repos[0]
                username = active_repo.username
                repo_name = active_repo.name
            else:
                if len(active_repos) > 1:
                    logger.error(
                        "Cannot determine repo automatically because there are multiple active repos: %s",
                        ", ".join(
                            [f"{repo.username}/{repo.name}" for repo in active_repos]
                        ),
                    )
                logger.error(
                    'You need to provide a repo by -r argument, such as "myuser/myrepo" or define a default repo in your config file'
                )
                sys.exit(-1)
    else:
        username, repo_name = parse_repo(
            repo if repo is not None else config.repo.default
        )
    return AuthConfig(
        token=config.access_token.token,
        username=username,
        repo=repo_name,
    )
