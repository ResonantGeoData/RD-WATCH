import json
import os
from pathlib import Path
from typing import TypedDict

from aiohttp import BasicAuth


class ConfigSchema(TypedDict):
    username: str
    password: str


CONFIG_PATH = (
    Path(
        os.environ.get("APPDATA")
        or os.environ.get("XDG_CONFIG_HOME")
        or os.path.join(os.environ["HOME"], ".config")
    )
    / "rdwatch"
)


def get_credentials() -> BasicAuth | None:
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH) as f:
        config: ConfigSchema = json.load(f)
    return BasicAuth(config["username"], config["password"])


def set_credentials(username: str, password: str):
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
    else:
        config = {}
    config["username"] = username
    config["password"] = password
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)
