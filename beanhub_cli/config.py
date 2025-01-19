import pathlib

from pydantic import BaseModel


class AccessToken(BaseModel):
    token: str


class Repository(BaseModel):
    default: str | None = None


class Config(BaseModel):
    access_token: AccessToken | None = None
    repo: Repository | None = None


def get_config_path() -> pathlib.Path:
    return pathlib.Path.home() / ".beanhub" / "config.toml"


def load_config(file_path: pathlib.Path | None = None) -> Config | None:
    import tomli

    if file_path is None:
        file_path = get_config_path()
    if not file_path.exists():
        return

    with file_path.open("rb") as fo:
        obj = tomli.load(fo)
        return Config.model_validate(obj)


def save_config(config: Config, file_path: pathlib.Path | None = None):
    import tomli_w

    if file_path is None:
        file_path = get_config_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    file_path.write_text("")
    file_path.chmod(0o600)
    # TODO: for now we save the config as plaintext. We should consider to use OS keychain service in the future
    #       for better security
    with file_path.open("wb") as fo:
        obj = config.model_dump(mode="json", exclude_none=True)
        tomli_w.dump(obj, fo)
