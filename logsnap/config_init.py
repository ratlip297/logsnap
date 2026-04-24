"""Generates a default logsnap config file interactively or with defaults."""

import json
import os
from logsnap.config import SnapConfig, ServiceConfig

DEFAULT_CONFIG_PATH = "logsnap.config.json"

DEFAULT_SERVICES = [
    ServiceConfig(
        name="app",
        log_path="/var/log/app/app.log",
        format="json",
        filters=["ERROR", "WARN"],
    ),
    ServiceConfig(
        name="nginx",
        log_path="/var/log/nginx/access.log",
        format="plaintext",
        filters=[],
    ),
]


def write_default_config(path: str = DEFAULT_CONFIG_PATH, overwrite: bool = False) -> str:
    """Write a default config file to the given path."""
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(
            f"Config already exists at '{path}'. Use overwrite=True to replace it."
        )

    config = SnapConfig(
        output_dir="./snapshots",
        timestamp_format="%Y%m%d_%H%M%S",
        services=DEFAULT_SERVICES,
        max_lines=None,
        compress=True,
    )

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    with open(path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)

    return path


def load_or_init_config(path: str = DEFAULT_CONFIG_PATH) -> SnapConfig:
    """Load config from file, or write defaults if it doesn't exist."""
    if not os.path.exists(path):
        write_default_config(path)
        print(f"[logsnap] No config found. Created default config at '{path}'.")
    return SnapConfig.from_file(path)
