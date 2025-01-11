import platform
import time
import urllib.parse
import webbrowser

import requests

from .cli import cli
from .environment import Environment
from .environment import pass_env


@cli.command(name="login", help="Login BeanHub")
@pass_env
def main(env: Environment):
    # TODO: check and see if we have already logged in

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
            env.logger.info("Session access granted")
            # TODO:
            print("@" * 20, resp.json()["token"])
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
