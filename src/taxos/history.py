"""Registro append-only de movimientos."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from platformdirs import user_data_path

from taxos.organizer import MoveAction


def history_file() -> Path:
    return user_data_path("taxos") / "history.jsonl"


def append_moves(actions: list[MoveAction]) -> Path:
    """Añade una línea JSON por movimiento. Devuelve la ruta del log."""
    path = history_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as fh:
        for action in actions:
            record = {
                "timestamp": now,
                "action": "move",
                "src": str(action.src),
                "dest": str(action.dest),
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
