import pathlib
import secrets

from pydantic import BaseSettings


class Settings(BaseSettings):
    SITE_NAME: str = "BeanHub Forms"
    DEBUG_LOG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_MAX_AGE: int = 14 * 24 * 60 * 60  # 14 days, in seconds
    BEANCOUNT_DIR: pathlib.Path = pathlib.Path.cwd()

    class Config:
        case_sensitive = True


settings = Settings()
