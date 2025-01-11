import platform
import time
import urllib.parse
import webbrowser

import requests

from .cli import cli
from .config import AccessToken
from .config import Config
from .config import get_config_path
from .config import load_config
from .config import save_config
from .environment import Environment
from .environment import pass_env


@cli.command(name="login", help="Login BeanHub")
@pass_env
def main(env: Environment):
    config_path = get_config_path()
    config = load_config()
    if config is not None and config.access_token is not None:
        # TODO: ask the user if they want to log out the original session first
        env.logger.error(
            "Already logged in, if you want to login again, please delete the config file at %s first",
            config_path,
        )
        return

    env.logger.info("Creating auth session ...")
    url = urllib.parse.urljoin(env.api_base_url, "v1/auth/sessions")
    resp = requests.post(url, json=dict(hostname=platform.node()))
    # TODO: check status and provide more user friendly error message?
    resp.raise_for_status()

    data = resp.json()
    session_id = data["id"]
    code = data["code"]
    poll_url = data["poll_url"]
    auth_url = data["auth_url"]

    env.logger.info(
        "Auth Code: %s",
        code,
    )
    if not webbrowser.open(data["auth_url"], new=2):
        env.logger.info(
            "Cannot open auth url, please open it manually in your browser: %s",
            auth_url,
        )

    env.logger.info(
        "Waiting granting access for current auth session: %s ...", session_id
    )
    while True:
        time.sleep(5)
        resp = requests.get(poll_url)
        if resp.status_code == 200:
            save_config(Config(access_token=AccessToken(token=resp.json()["token"])))
            env.logger.info("Session access granted, saved config to %s", config_path)
            break
        elif resp.status_code == 202:
            env.logger.debug("Session access not granted yet, try again later")
        else:
            env.logger.error(
                "Failed to fetch token, encountered unexpected status code %s",
                resp.status_code,
            )
            return

    env.logger.info("done")
