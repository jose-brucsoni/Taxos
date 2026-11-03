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
    conflict: bool = False


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


def _ensure_dir(path: Path) -> list[Path]:
    """Crea `path` y devuelve solo los directorios que no existían."""
    created: list[Path] = []
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    for directory in reversed(missing):
        directory.mkdir(exist_ok=True)
        created.append(directory)
    return created


def _rollback_empty(dirs: list[Path]) -> None:
    for directory in reversed(dirs):
        try:
            directory.rmdir()
        except OSError:
            break


def apply_plan(
    actions: list[MoveAction],
    created_dirs: list[Path] | None = None,
) -> list[MoveAction]:
    """Crea carpetas y mueve archivos. Continúa si un archivo falla.

    Si se pasa `created_dirs`, añade las carpetas creadas por los movimientos
    que sí se completaron.
    """
    done: list[MoveAction] = []
    for action in actions:
        new_dirs: list[Path] = []
        try:
            if not action.src.is_file():
                continue
            new_dirs = _ensure_dir(action.dest.parent)
            dest = _unique_dest(action.dest, set())
            shutil.move(str(action.src), str(dest))
            done.append(MoveAction(src=action.src, dest=dest))
            if created_dirs is not None:
                created_dirs.extend(new_dirs)
        except OSError:
            _rollback_empty(new_dirs)
            continue
    return done
