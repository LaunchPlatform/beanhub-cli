import pathlib
import secrets

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)
    SITE_NAME: str = "BeanHub Forms"
    DEBUG_LOG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_MAX_AGE: int = 14 * 24 * 60 * 60  # 14 days, in seconds
    BEANCOUNT_DIR: pathlib.Path = pathlib.Path.cwd()


settings = Settings()
