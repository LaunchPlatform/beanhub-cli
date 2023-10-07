import pathlib
import secrets
import typing

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)
    SITE_NAME: str = "BeanHub Forms"
    DEBUG_LOG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_MAX_AGE: int = 14 * 24 * 60 * 60  # 14 days, in seconds
    BEANCOUNT_DIR: pathlib.Path = pathlib.Path.cwd()


# Do not import and access this directly, use settings instead
_settings = Settings()


class SettingsProxy:
    def __init__(self, get_settings: typing.Callable[[], Settings]):
        self._get_settings = get_settings

    def __getattr__(self, item: str) -> typing.Any:
        global_settings = self._get_settings()
        return getattr(global_settings, item)


settings: Settings = SettingsProxy(lambda: _settings)
