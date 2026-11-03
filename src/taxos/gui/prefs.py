"""Preferencias de la GUI (tema, etc.)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

_VALID_MODES = frozenset({"System", "Light", "Dark"})
_DEFAULTS: dict[str, Any] = {"appearance_mode": "System"}


def _prefs_path() -> Path:
    return Path(user_config_dir("taxos")) / "gui.json"


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
    mode = data.get("appearance_mode", "System")
    if mode not in _VALID_MODES:
        mode = "System"
    return {"appearance_mode": mode}


def save_gui_prefs(prefs: dict[str, Any]) -> None:
    """Guarda preferencias GUI en el directorio de config del usuario."""
    path = _prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = prefs.get("appearance_mode", "System")
    if mode not in _VALID_MODES:
        mode = "System"
    payload = {"appearance_mode": mode}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
