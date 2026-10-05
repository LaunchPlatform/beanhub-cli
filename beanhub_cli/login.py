import logging
import platform
import sys
import time
import webbrowser

import httpx

from .api_helpers import handle_api_exception
from .cli import cli
from .config import AccessToken
from .config import Config
from .config import get_config_path
from .config import load_config
from .config import save_config
from .environment import Environment
from .environment import pass_env
from .http_client import make_auth_client
from .http_client import make_client
from .internal_api.api.auth import create_auth_session
from .internal_api.api.auth import poll_auth_session
from .internal_api.client import Client
from .internal_api.models import AuthSessionNotReadyResponse
from .internal_api.models import AuthSessionPollResponse
from .internal_api.models import AuthSessionRequest
from .internal_api.models import GenericError
from .internal_api.types import Response

logger = logging.getLogger(__name__)


def run_login(client: Client):
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
@handle_api_exception(logger)
def main(env: Environment):
    config_path = get_config_path()
    config = load_config()
    if config is not None and config.access_token is not None:
        logger.error(
            'Already logged in. Run "bh logout" to remove the saved access token at %s first',
            config_path,
        )
        sys.exit(-1)

    logger.info("Creating auth session ...")
    with make_client(base_url=env.api_base_url) as client:
        client.raise_on_unexpected_status = True
        run_login(client=client)


def _forget_local_token(config: Config):
    config_path = get_config_path()
    config.access_token = None
    if config.model_dump(exclude_none=True):
        save_config(config)
    elif config_path.exists():
        config_path.unlink()


def _revoke_access_token(base_url: str, token: str) -> httpx.Response:
    with make_auth_client(base_url=base_url, token=token) as client:
        return client.get_httpx_client().request("DELETE", "/v1/auth/token")


@cli.command(name="logout", help="Log out of your BeanHub account")
@pass_env
def logout(env: Environment):
    config_path = get_config_path()
    config = load_config()
    if config is None or config.access_token is None:
        logger.info("Not logged in")
        return

    try:
        resp = _revoke_access_token(env.api_base_url, config.access_token.token)
    except httpx.RequestError:
        logger.error(
            "Could not reach BeanHub to revoke the access token, so you are still logged in. Try again."
        )
        sys.exit(-1)

    if resp.status_code == 204:
        _forget_local_token(config)
        logger.info(
            "Logged out. Revoked the access token and removed it from %s",
            config_path,
        )
        return
    if resp.status_code == 401:
        _forget_local_token(config)
        logger.info(
            "Logged out. The access token was already invalid. Removed it from %s",
            config_path,
        )
        return
    if resp.status_code == 404:
        _forget_local_token(config)
        logger.warning(
            "Logged out on this computer. Delete this token at %s so it stops working.",
            "https://app.beanhub.io/access-tokens/",
        )
        return

    logger.error(
        "Could not revoke the access token (HTTP %s), so you are still logged in. Try again.",
        resp.status_code,
    )
    sys.exit(-1)
