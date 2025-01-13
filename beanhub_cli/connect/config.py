import dataclasses
import sys

from ..config import load_config
from ..environment import Environment


@dataclasses.dataclass
class ConnectConfig:
    token: str
    repo: str


# TODO: maybe extract this part to a shared env for connect command?
def ensure_config(env: Environment, repo: str | None) -> ConnectConfig:
    config = load_config()
    if config is None or config.access_token is None:
        env.logger.error(
            'You need to login into your BeanHub account with "bh login" command first'
        )
        sys.exit(-1)
    if repo is None and (config.repo is None or config.repo.default is None):
        env.logger.error(
            'You need to provide a repo by -r argument, such as "myuser/myrepo" or define a default repo in your config file'
        )
        sys.exit(-1)
    return ConnectConfig(
        token=config.access_token.token,
        repo=repo if repo is not None else config.repo.default,
    )
