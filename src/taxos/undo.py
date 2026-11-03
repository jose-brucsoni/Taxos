"""Deshacer el último lote de movimientos."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from taxos.organizer import MoveAction, _unique_dest


def build_undo_plan(batch: list[dict[str, Any]]) -> list[MoveAction]:
    """Invierte dest → src solo si el destino actual aún existe."""
    reserved: set[Path] = set()
    actions: list[MoveAction] = []

    for record in reversed(batch):
        dest = Path(str(record.get("dest", "")))
        src = Path(str(record.get("src", "")))
        if not dest.is_file():
            continue
        target = _unique_dest(src, reserved)
        reserved.add(target)
        actions.append(MoveAction(src=dest, dest=target))

    return actions


def apply_undo(actions: list[MoveAction]) -> list[MoveAction]:
    """Restaura archivos. Continúa si uno falla."""
    done: list[MoveAction] = []
    for action in actions:
        try:
            if not action.src.is_file():
                continue
            action.dest.parent.mkdir(parents=True, exist_ok=True)
            dest = _unique_dest(action.dest, set())
            shutil.move(str(action.src), str(dest))
            done.append(MoveAction(src=action.src, dest=dest))
        except OSError:
            continue
    return done
