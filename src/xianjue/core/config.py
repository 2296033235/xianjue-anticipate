"""Configuration manager: load, merge defaults, persist user overrides."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "default_config.json"
_USER_PATH = Path.home() / ".xianjue" / "config.json"


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base, returning a new dict."""
    result = base.copy()
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    """Wraps a merged config dict and provides typed accessors."""

    def __init__(self) -> None:
        self._defaults = self._load_defaults()
        self._user = self._load_user()
        self._data = _deep_merge(self._defaults, self._user)

    def _load_defaults(self) -> dict:
        if _DEFAULT_PATH.exists():
            return json.loads(_DEFAULT_PATH.read_text(encoding="utf-8"))
        return {}

    def _load_user(self) -> dict:
        if _USER_PATH.exists():
            return json.loads(_USER_PATH.read_text(encoding="utf-8"))
        return {}

    def save(self) -> None:
        """Persist only user-level overrides (values that differ from defaults)."""
        _USER_PATH.parent.mkdir(parents=True, exist_ok=True)
        _USER_PATH.write_text(
            json.dumps(self._user, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get(self, dot_path: str, default: Any = None) -> Any:
        """Access nested values via dot notation, e.g. 'model.cloud.api_key'."""
        keys = dot_path.split(".")
        node: Any = self._data
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node

    def set(self, dot_path: str, value: Any, persist: bool = True) -> None:
        """Set a nested value and optionally persist to user config."""
        keys = dot_path.split(".")
        # Walk/create the path in _user so it overrides the default.
        node = self._user
        for key in keys[:-1]:
            if key not in node or not isinstance(node[key], dict):
                node[key] = {}
            node = node[key]
        node[keys[-1]] = value
        # Update the merged view.
        self._data = _deep_merge(self._defaults, self._user)
        if persist:
            self.save()

    @property
    def data(self) -> dict:
        return self._data.copy()
