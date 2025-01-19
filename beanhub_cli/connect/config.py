import dataclasses
import logging
import sys
import typing

from ..config import load_config
from ..environment import Environment

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ConnectConfig:
    token: str
    username: str
    repo: str


def parse_repo(repo: str | None) -> typing.Tuple[str | None, str | None]:
    if repo is None:
        return None, None
    return tuple(repo.split("/", 1))


# TODO: maybe extract this part to a shared env for connect command?
def ensure_config(env: Environment, repo: str | None) -> ConnectConfig:
    config = load_config()
    if config is None or config.access_token is None:
        logger.error(
            'You need to login into your BeanHub account with "bh login" command first'
        )
        sys.exit(-1)
    if repo is None and (config.repo is None or config.repo.default is None):
        logger.info(
            "No repo provided, try to determine which repo to use automatically ..."
        )

        from ..internal_api import AuthenticatedClient
        from ..internal_api.api.repo import list_repo

        with AuthenticatedClient(
            base_url=env.api_base_url, token=config.access_token.token
        ) as client:
            client.raise_on_unexpected_status = True
            resp = list_repo.sync(client=client)
            active_repos = list(filter(lambda: repo.active, resp.repositories))
            if len(active_repos) == 1:
                active_repo = active_repos[0]
                username = active_repo.username
                repo_name = active_repo.name
            else:
                logger.error(
                    'You need to provide a repo by -r argument, such as "myuser/myrepo" or define a default repo in your config file'
                )
                sys.exit(-1)
    else:
        username, repo_name = parse_repo(
            repo if repo is not None else config.repo.default
        )
    return ConnectConfig(
        token=config.access_token.token,
        username=username,
        repo=repo_name,
    )
