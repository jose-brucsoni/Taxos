"""Deshacer el último lote de movimientos."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from taxos.organize_modes import restore_tags
from taxos.organizer import MoveAction, _unique_dest


def _same_path(left: Path, right: Path) -> bool:
    return left.expanduser().resolve() == right.expanduser().resolve()


def build_undo_plan(batch: list[dict[str, Any]]) -> list[MoveAction]:
    """Invierte dest → src solo si el destino actual aún existe.

    Si la ruta original está ocupada, elige otro nombre y marca `conflict`.
    """
    reserved: set[Path] = set()
    actions: list[MoveAction] = []

    for record in reversed(batch):
        if record.get("action") not in {None, "move"}:
            continue
        dest = Path(str(record.get("dest", "")))
        src = Path(str(record.get("src", "")))
        if not dest.is_file():
            continue
        target = _unique_dest(src, reserved)
        reserved.add(target)
        actions.append(
            MoveAction(src=dest, dest=target, conflict=not _same_path(target, src))
        )

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
            conflict = action.conflict or not _same_path(dest, action.dest)
            done.append(MoveAction(src=action.src, dest=dest, conflict=conflict))
        except OSError:
            continue
    return done


def remove_empty_created_dirs(dirs: list[Path]) -> list[Path]:
    """Borra carpetas creadas por el lote si quedaron vacías. Las más profundas primero."""
    unique: list[Path] = []
    seen: set[str] = set()
    for directory in dirs:
        key = str(directory)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(directory)
    unique.sort(key=lambda path: len(path.parts), reverse=True)

    removed: list[Path] = []
    for directory in unique:
        try:
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
                removed.append(directory)
        except OSError:
            continue
    return removed


@dataclass(frozen=True)
class UndoSummary:
    actions: list[MoveAction]
    created_dirs: list[Path]
    tags: list[dict[str, Any]]
    cleanup_dirs: list[Path]

    @property
    def available(self) -> bool:
        return bool(self.actions or self.tags or self.cleanup_dirs)


def summarize_batch(batch: list[dict[str, Any]]) -> UndoSummary:
    """Qué se puede revertir de un lote (movimientos, etiquetas y carpetas vacías)."""
    moves = [record for record in batch if record.get("action") in {None, "move"}]
    actions = build_undo_plan(moves)
    created = [
        Path(str(record.get("path", "")))
        for record in batch
        if record.get("action") == "mkdir" and record.get("path")
    ]
    tags = [record for record in batch if record.get("action") == "tags"]
    cleanup = [
        directory
        for directory in created
        if directory.is_dir() and not any(directory.iterdir())
    ]
    return UndoSummary(
        actions=actions,
        created_dirs=created,
        tags=tags,
        cleanup_dirs=cleanup,
    )


@dataclass(frozen=True)
class UndoOutcome:
    restored: list[MoveAction]
    removed_dirs: list[Path]
    tags_restored: int

    @property
    def did_something(self) -> bool:
        return bool(self.restored or self.removed_dirs or self.tags_restored)


def execute_undo(summary: UndoSummary) -> UndoOutcome:
    """Restaura archivos, etiquetas y carpetas vacías creadas en el lote."""
    restored = apply_undo(summary.actions)
    removed = remove_empty_created_dirs(summary.created_dirs)
    tags_restored = 0
    for record in summary.tags:
        path = Path(str(record.get("path", "")))
        if not str(path):
            continue
        previous = record.get("previous")
        if previous is not None and not isinstance(previous, str):
            continue
        if restore_tags(path, previous):
            tags_restored += 1
    return UndoOutcome(
        restored=restored,
        removed_dirs=removed,
        tags_restored=tags_restored,
    )
