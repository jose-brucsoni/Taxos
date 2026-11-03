"""Registro append-only de acciones Taxos."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platformdirs import user_data_path

from taxos.cleaner import TrashCandidate
from taxos.organizer import MoveAction


def history_file() -> Path:
    return user_data_path("taxos") / "history.jsonl"


def _append_records(records: list[dict[str, Any]]) -> Path:
    path = history_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_moves(actions: list[MoveAction]) -> Path:
    """Añade una línea JSON por movimiento."""
    now = _now()
    records = [
        {
            "timestamp": now,
            "action": "move",
            "src": str(action.src),
            "dest": str(action.dest),
        }
        for action in actions
    ]
    return _append_records(records)


def append_trash(candidates: list[TrashCandidate]) -> Path:
    """Añade una línea JSON por archivo enviado a papelera."""
    now = _now()
    records = [
        {
            "timestamp": now,
            "action": "trash",
            "src": str(candidate.path),
            "reason": candidate.reason,
        }
        for candidate in candidates
    ]
    return _append_records(records)


def append_undos(actions: list[MoveAction]) -> Path:
    """Añade una línea JSON por deshacer (dest→src restaurado)."""
    now = _now()
    records = [
        {
            "timestamp": now,
            "action": "undo",
            "src": str(action.src),
            "dest": str(action.dest),
        }
        for action in actions
    ]
    return _append_records(records)


def read_records() -> list[dict[str, Any]]:
    """Lee todo el historial; ignora líneas corruptas."""
    path = history_file()
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def last_move_batch() -> list[dict[str, Any]]:
    """Último lote de movimientos con el mismo timestamp."""
    moves = [r for r in read_records() if r.get("action") == "move"]
    if not moves:
        return []
    last_ts = moves[-1].get("timestamp")
    batch: list[dict[str, Any]] = []
    for record in reversed(moves):
        if record.get("timestamp") != last_ts:
            break
        batch.append(record)
    batch.reverse()
    return batch
