import logging
import platform
import sys
import time
import webbrowser

from .api_helpers import handle_api_exception
from .cli import cli
from .config import AccessToken
from .config import Config
from .config import get_config_path
from .config import load_config
from .config import save_config
from .environment import Environment
from .environment import pass_env
from .utils import check_imports
from .utils import ExtraDepsSet

logger = logging.getLogger(__name__)


def run_login(client: "Client"):
    from .internal_api.api.auth import create_auth_session
    from .internal_api.api.auth import poll_auth_session
    from .internal_api.models import AuthSessionNotReadyResponse
    from .internal_api.models import AuthSessionPollResponse
    from .internal_api.models import AuthSessionRequest
    from .internal_api.models import GenericError
    from .internal_api.types import Response

    auth_session = create_auth_session.sync(
        body=AuthSessionRequest(hostname=platform.node()), client=client
    )
    logger.info(
        "Auth Code: %s",
        auth_session.code,
    )
    if not webbrowser.open(auth_session.auth_url, new=2):
        logger.info(
            "Cannot open auth url, please open it manually in your browser: %s",
            auth_session.auth_url,
        )

    logger.info(
        "Waiting granting access for current auth session: %s ...", auth_session.id
    )
    while True:
        time.sleep(5)
        # TODO: provide a websocket for updates in the future
        resp: Response[
            AuthSessionNotReadyResponse | AuthSessionPollResponse | GenericError
        ] = poll_auth_session.sync_detailed(
            secret_token=auth_session.secret_token,
            auth_session_id=auth_session.id,
            client=client,
        )
        if resp.status_code == 200:
            payload: AuthSessionPollResponse = resp.parsed
            save_config(
                Config(
                    access_token=AccessToken(token=payload.token),
                )
            )
            logger.info("Session access granted, saved config to %s", get_config_path())
            break
        elif resp.status_code == 202:
            logger.debug("Session access not granted yet, try again later")
        else:
            logger.error(
                "Failed to fetch token, encountered unexpected status code %s",
                resp.status_code,
            )
            return
    logger.info("done")


@cli.command(name="login", help="Login your BeanHub account")
@pass_env
@check_imports(ExtraDepsSet.LOGIN, logger)
@handle_api_exception(logger)
def main(env: Environment):
    from .internal_api.client import Client

    config_path = get_config_path()
    config = load_config()
    if config is not None and config.access_token is not None:
        # TODO: ask the user if they want to log out the original session first
        logger.error(
            "Already logged in, if you want to login again, please delete the config file at %s first",
            config_path,
        )
        sys.exit(-1)

    logger.info("Creating auth session ...")
    with Client(base_url=env.api_base_url) as client:
        client.raise_on_unexpected_status = True
        run_login(client=client)
