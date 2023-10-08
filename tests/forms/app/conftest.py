import base64
import hashlib
import json
import os
import typing

import itsdangerous
import pytest
from fastapi import FastAPI
from itsdangerous.url_safe import URLSafeTimedSerializer
from starlette.testclient import TestClient

from . import types_def
from beanhub_cli.forms.app import settings as settings_module
from beanhub_cli.forms.app.main import make_app


@pytest.fixture
def app() -> FastAPI:
    return make_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def settings() -> settings_module.Settings:
    old_settings = settings_module._settings
    settings_module._settings = settings_module.Settings()
    yield settings_module._settings
    settings_module._settings = old_settings


@pytest.fixture
def raw_csrf_token() -> str:
    return hashlib.sha1(os.urandom(64)).hexdigest()


@pytest.fixture
def csrf_token(raw_csrf_token: str, settings: settings_module.Settings) -> str:
    s = URLSafeTimedSerializer(settings.SECRET_KEY, salt="wtf-csrf-token")
    return s.dumps(raw_csrf_token)


@pytest.fixture
def session_signer(settings: settings_module.Settings) -> itsdangerous.TimestampSigner:
    return itsdangerous.TimestampSigner(str(settings.SECRET_KEY))


@pytest.fixture
def make_session(
    session_signer: itsdangerous.TimestampSigner,
) -> types_def.MakeSession:
    def _make_session(**data: typing.Any) -> str:
        json_data: bytes = json.dumps(data).encode("utf8")
        signed_data = session_signer.sign(base64.b64encode(json_data))
        return signed_data.decode("utf8")

    return _make_session


@pytest.fixture
def make_session_cookies(
    make_session: typing.Callable[[typing.Dict[str, typing.Any]], str],
    raw_csrf_token: str,
) -> types_def.MakeSessionCookies:
    def _make_session_cookies(
        _add_csrf_token: bool = True, **data: str
    ) -> typing.Dict[str, typing.Any]:
        session_data = data
        if _add_csrf_token:
            session_data |= dict(csrf_token=raw_csrf_token)
        return dict(session=make_session(**data))

    return _make_session_cookies
