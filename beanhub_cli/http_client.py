from functools import lru_cache
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

from .internal_api.client import AuthenticatedClient
from .internal_api.client import Client

PACKAGE_NAME = "beanhub-cli"
CLIENT_VERSION_HEADER = "X-BeanHub-CLI-Version"


@lru_cache
def get_cli_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"


def get_client_headers() -> dict[str, str]:
    cli_version = get_cli_version()
    return {
        "User-Agent": f"{PACKAGE_NAME}/{cli_version}",
        CLIENT_VERSION_HEADER: cli_version,
    }


def make_client(base_url: str) -> Client:
    return Client(base_url=base_url, headers=get_client_headers())


def make_auth_client(base_url: str, token: str) -> AuthenticatedClient:
    return AuthenticatedClient(
        base_url=base_url,
        prefix="",
        auth_header_name="access-token",
        token=token,
        headers=get_client_headers(),
    )
