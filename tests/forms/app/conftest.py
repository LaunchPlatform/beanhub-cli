import copy

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

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
