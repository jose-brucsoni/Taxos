"""Preferencias de la GUI (tema, onboarding, etc.)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

_VALID_MODES = frozenset({"System", "Light", "Dark"})
ONBOARDING_FLAGS = frozenset({"tutorial_seen", "preview_tip_seen", "undo_tip_seen"})
_DEFAULTS: dict[str, Any] = {
    "appearance_mode": "Light",
    "tutorial_seen": False,
    "preview_tip_seen": False,
    "undo_tip_seen": False,
}


def _prefs_path() -> Path:
    return Path(user_config_dir("taxos")) / "gui.json"


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    mode = data.get("appearance_mode", _DEFAULTS["appearance_mode"])
    if mode not in _VALID_MODES:
        mode = "Light"
    return {
        "appearance_mode": mode,
        "tutorial_seen": _as_bool(data.get("tutorial_seen"), False),
        "preview_tip_seen": _as_bool(data.get("preview_tip_seen"), False),
        "undo_tip_seen": _as_bool(data.get("undo_tip_seen"), False),
    }


def load_gui_prefs() -> dict[str, Any]:
    """Carga preferencias GUI; valores por defecto si no existen o son inválidos."""
    path = _prefs_path()
    if not path.is_file():
        return dict(_DEFAULTS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(_DEFAULTS)
    if not isinstance(data, dict):
        return dict(_DEFAULTS)
    return _normalize(data)


def save_gui_prefs(prefs: dict[str, Any]) -> None:
    """Guarda preferencias GUI haciendo merge con lo existente."""
    merged = _normalize({**load_gui_prefs(), **prefs})
    path = _prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")


def update_gui_prefs(**kwargs: Any) -> dict[str, Any]:
    """Parche parcial de preferencias; devuelve el estado guardado."""
    unknown = set(kwargs) - set(_DEFAULTS)
    if unknown:
        raise ValueError(f"Preferencias desconocidas: {', '.join(sorted(unknown))}")
    save_gui_prefs(kwargs)
    return load_gui_prefs()
