from importlib.metadata import version

from beanhub_cli.http_client import CLIENT_VERSION_HEADER
from beanhub_cli.http_client import get_client_headers
from beanhub_cli.http_client import make_auth_client
from beanhub_cli.http_client import make_client


def test_get_client_headers():
    cli_version = version("beanhub-cli")
    headers = get_client_headers()
    assert headers == {
        "User-Agent": f"beanhub-cli/{cli_version}",
        CLIENT_VERSION_HEADER: cli_version,
    }


def test_make_client_includes_version_headers():
    client = make_client(base_url="https://api.beanhub.io")
    with client:
        httpx_client = client.get_httpx_client()
        assert httpx_client.headers["User-Agent"] == get_client_headers()["User-Agent"]
        assert (
            httpx_client.headers[CLIENT_VERSION_HEADER]
            == get_client_headers()[CLIENT_VERSION_HEADER]
        )


def test_make_auth_client_includes_version_headers():
    client = make_auth_client(base_url="https://api.beanhub.io", token="test-token")
    with client:
        httpx_client = client.get_httpx_client()
        assert httpx_client.headers["access-token"] == "test-token"
        assert httpx_client.headers["User-Agent"] == get_client_headers()["User-Agent"]
        assert (
            httpx_client.headers[CLIENT_VERSION_HEADER]
            == get_client_headers()[CLIENT_VERSION_HEADER]
        )
