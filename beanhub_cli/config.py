import pathlib
import tomllib

import tomli_w
from pydantic import BaseModel


class AccessToken(BaseModel):
    token: str


class Config(BaseModel):
    access_token: AccessToken | None = None


def get_config_path() -> pathlib.Path:
    return pathlib.Path.home() / ".beanhub" / "config.toml"


def load_config(file_path: pathlib.Path | None = None) -> Config | None:
    if file_path is None:
        file_path = get_config_path()
    if not file_path.exists():
        return

    with file_path.open("rb") as fo:
        obj = tomllib.load(fo)
        return Config.model_validate(obj)


def save_config(config: Config, file_path: pathlib.Path | None = None):
    if file_path is None:
        file_path = get_config_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    file_path.write_text("")
    file_path.chmod(0o400)
    # TODO: for now we save the config as plaintext. We should consider to use OS keychain service in the future
    #       for better security
    with file_path.open("wb") as fo:
        obj = config.model_dump(mode="json")
        tomli_w.dump(obj, fo)
