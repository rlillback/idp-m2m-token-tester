"""Read a .env file into a dict. It is never exported to os.environ and never written."""

from __future__ import annotations

import os
import stat
import sys
from collections.abc import Mapping
from pathlib import Path

from dotenv import dotenv_values

from .errors import ConfigError

DEFAULT_ENV_FILE = Path(".env")


def load_env_file(path: Path, explicit: bool) -> dict[str, str]:
    """Return the file values. A missing default is ignored; a missing explicit file errors."""
    if not path.is_file():
        if explicit:
            raise ConfigError(f"Env file not found: {path}")
        return {}
    _warn_if_loose(path)
    return {k: v for k, v in dotenv_values(path).items() if v is not None}


def merged_environment(
    env_file: Path | None, environ: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Real environment variables take precedence over the .env file."""
    base = dict(os.environ if environ is None else environ)
    file_values = load_env_file(env_file or DEFAULT_ENV_FILE, explicit=env_file is not None)
    return {**file_values, **base}


def _warn_if_loose(path: Path) -> None:
    try:
        mode = path.stat().st_mode
    except OSError:
        return
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        print(
            f"Warning: {path} is readable by other users; run: chmod 600 {path}",
            file=sys.stderr,
        )
