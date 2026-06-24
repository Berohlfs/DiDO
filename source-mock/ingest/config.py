"""Configuration loading: ``.env`` file + ``os.environ`` overrides."""
from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass
class Config:
    base_url: str
    client_id: str
    client_secret: str
    scopes: str = "read write"
    sources_dir: str = "sources"
    log_dir: str = ".ingest-logs"
    max_bytes: int = 1_048_576


# Maps env/.env keys to Config fields.
_REQUIRED = {
    "GBRAIN_BASE_URL": "base_url",
    "GBRAIN_CLIENT_ID": "client_id",
    "GBRAIN_CLIENT_SECRET": "client_secret",
}
_OPTIONAL = {
    "GBRAIN_SCOPES": "scopes",
    "GBRAIN_SOURCES_DIR": "sources_dir",
    "GBRAIN_LOG_DIR": "log_dir",
    "GBRAIN_MAX_BYTES": "max_bytes",
}


def _parse_env_file(path: str) -> dict:
    values: dict = {}
    if not os.path.isfile(path):
        return values
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)  # split on first '='
            values[key.strip()] = value.strip()
    return values


def load_config(env_path: str = ".env") -> Config:
    """Load config from ``env_path``; real environment variables override it."""
    file_values = _parse_env_file(env_path)

    def lookup(key: str):
        # Real env wins over the .env file.
        return os.environ.get(key, file_values.get(key))

    fields: dict = {}
    missing: list = []
    for key, field in _REQUIRED.items():
        value = lookup(key)
        if value is None or value == "":
            missing.append(key)
        else:
            fields[field] = value
    if missing:
        raise ConfigError(
            "missing required configuration: " + ", ".join(missing) +
            f" (set them in {env_path} or the environment)"
        )

    for key, field in _OPTIONAL.items():
        value = lookup(key)
        if value is None or value == "":
            continue
        if field == "max_bytes":
            try:
                fields[field] = int(value)
            except ValueError:
                raise ConfigError(f"{key} must be an integer, got {value!r}")
        else:
            fields[field] = value

    return Config(**fields)
