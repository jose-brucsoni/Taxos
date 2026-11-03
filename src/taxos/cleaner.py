"""Candidatos seguros a enviar a la papelera."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from send2trash import send2trash

TRASH_EXTENSIONS = {".tmp", ".crdownload", ".part", ".download"}


@dataclass(frozen=True)
class TrashCandidate:
    path: Path
    size: int
    reason: str


def _is_candidate(path: Path, size: int) -> str | None:
    name = path.name
    suffix = path.suffix.lower()
    if size == 0:
        return "vacío"
    if suffix in TRASH_EXTENSIONS:
        return f"extensión {suffix}"
    if name.startswith(".~lock."):
        return "lock LibreOffice"
    return None


def find_candidates(root: Path) -> list[TrashCandidate]:
    """Busca candidatos solo en la raíz de `root`."""
    if not root.is_dir():
        return []

    found: list[TrashCandidate] = []
    for item in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_file():
            continue
        try:
            size = item.stat().st_size
        except OSError:
            continue
        reason = _is_candidate(item, size)
        if reason:
            found.append(TrashCandidate(path=item, size=size, reason=reason))
    return found


def apply_trash(candidates: list[TrashCandidate]) -> list[TrashCandidate]:
    """Envía a la papelera. Continúa si uno falla."""
    done: list[TrashCandidate] = []
    for candidate in candidates:
        try:
            if not candidate.path.is_file():
                continue
            send2trash(str(candidate.path))
            done.append(candidate)
        except OSError:
            continue
    return done
