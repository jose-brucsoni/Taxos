"""Plan y aplicación de movimientos por categoría."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from taxos.scanner import FileEntry


@dataclass(frozen=True)
class MoveAction:
    src: Path
    dest: Path


def _unique_dest(dest: Path, reserved: set[Path]) -> Path:
    """Evita colisiones con archivos existentes o destinos ya reservados en el plan."""
    if not dest.exists() and dest not in reserved:
        return dest

    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    n = 1
    while True:
        candidate = parent / f"{stem}_{n}{suffix}"
        if not candidate.exists() and candidate not in reserved:
            return candidate
        n += 1


def build_plan(
    root: Path,
    classified: list[tuple[FileEntry, str]],
) -> list[MoveAction]:
    """Construye movimientos raíz → root/<categoria>/nombre (ignora dotfiles)."""
    root = root.resolve()
    reserved: set[Path] = set()
    actions: list[MoveAction] = []

    for entry, category in classified:
        if entry.name.startswith("."):
            continue
        dest_dir = root / category
        dest = _unique_dest(dest_dir / entry.name, reserved)
        reserved.add(dest)
        if dest.resolve() == entry.path.resolve():
            continue
        actions.append(MoveAction(src=entry.path, dest=dest))

    return actions


def apply_plan(actions: list[MoveAction]) -> list[MoveAction]:
    """Crea carpetas y mueve archivos. Continúa si un archivo falla."""
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
