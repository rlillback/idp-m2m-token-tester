"""Resolve settings from environment variables, falling back to a prompt.

Nothing is persisted. Secrets are prompted with getpass so they are not echoed.
"""

from __future__ import annotations

import getpass
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .errors import ConfigError


@dataclass(frozen=True)
class Setting:
    key: str
    env: str
    label: str
    secret: bool = False
    required: bool = True
    default: str | None = None
    choices: tuple[str, ...] | None = None
    applies: Callable[[Mapping[str, str]], bool] | None = None


def mask(value: str) -> str:
    return "*" * 8 if value else ""


def resolve_settings(
    settings: list[Setting],
    environ: Mapping[str, str] | None = None,
    prompt: Callable[[str], str] | None = None,
    prompt_secret: Callable[[str], str] | None = None,
) -> dict[str, str]:
    """Return {key: value}. Settings are evaluated in order so `applies` can use earlier ones."""
    env = os.environ if environ is None else environ
    prompt = prompt or input
    prompt_secret = prompt_secret or getpass.getpass
    values: dict[str, str] = {}
    for s in settings:
        if s.applies is not None and not s.applies(values):
            continue
        value = (env.get(s.env) or "").strip()
        if not value:
            value = _ask(s, prompt, prompt_secret)
        if not value and s.default is not None:
            value = s.default
        if not value and s.required:
            raise ConfigError(f"{s.label} is required (set {s.env}).")
        if value and s.choices and value not in s.choices:
            raise ConfigError(f"{s.env} must be one of: {', '.join(s.choices)}.")
        if value:
            values[s.key] = value
    return values


def _ask(s: Setting, prompt: Callable[[str], str], prompt_secret: Callable[[str], str]) -> str:
    hint = ""
    if s.default is not None:
        hint = f" [{s.default}]"
    elif not s.required:
        hint = " (optional, Enter to skip)"
    text = f"{s.label} ({s.env}){hint}: "
    return (prompt_secret(text) if s.secret else prompt(text)).strip()
