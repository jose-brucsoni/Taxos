"""Candidatos seguros a enviar a la papelera (reglas por SO, recursivo)."""

from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from send2trash import send2trash

TRASH_EXTENSIONS = {".tmp", ".temp", ".crdownload", ".part", ".download"}
_SORT_KEYS = frozenset({"name", "size", "extension", "reason"})


@dataclass(frozen=True)
class TrashCandidate:
    path: Path
    size: int
    reason: str
    root: Path | None = None

    @property
    def extension(self) -> str:
        suffix = self.path.suffix.lower()
        return suffix[1:] if suffix.startswith(".") else suffix

    def relative_label(self) -> str:
        base = self.root
        if base is not None:
            try:
                return str(self.path.relative_to(base))
            except ValueError:
                pass
        return str(self.path)


def _is_windows(platform: str | None = None) -> bool:
    return (platform or sys.platform).startswith("win")


def _candidate_reason(path: Path, size: int, *, platform: str | None = None) -> str | None:
    name = path.name
    lower = name.lower()
    suffix = path.suffix.lower()

    if size == 0:
        return "vacío"
    if suffix in TRASH_EXTENSIONS:
        return f"extensión {suffix}"
    if name.startswith(".~lock."):
        return "lock LibreOffice"

    if _is_windows(platform):
        if lower in {"thumbs.db", "ehthumbs.db", "desktop.ini"}:
            return f"basura Windows ({name})"
        if name.startswith("~$"):
            return "temporal Office"
        if suffix == ".stackdump":
            return "extensión .stackdump"
    else:
        if name.endswith("~"):
            return "backup editor (*~)"
        if lower.endswith((".swp", ".swo")) and name.startswith("."):
            return "swap Vim"
        if lower == ".ds_store":
            return "basura macOS/Finder"
        if lower.startswith(".fuse_hidden"):
            return "resto FUSE"

    return None


def default_clean_roots(*, platform: str | None = None) -> list[Path]:
    """Raíces de temp/caché del usuario actual (sin carpetas de sistema)."""
    roots: list[Path] = []
    home = Path.home().resolve()

    if _is_windows(platform):
        for key in ("TEMP", "TMP"):
            raw = os.environ.get(key, "").strip()
            if raw:
                roots.append(Path(raw))
        local = os.environ.get("LOCALAPPDATA", "").strip()
        if local:
            roots.append(Path(local) / "Temp")
    else:
        xdg = os.environ.get("XDG_CACHE_HOME", "").strip()
        if xdg:
            roots.append(Path(xdg))
        else:
            roots.append(home / ".cache")
        try:
            tmp = Path(tempfile.gettempdir())
            resolved = tmp.resolve()
            if resolved == home or home in resolved.parents or resolved in home.parents:
                roots.append(tmp)
            # /tmp/.../user-owned dirs under home only; skip global /tmp
        except OSError:
            pass

    unique: list[Path] = []
    seen: set[Path] = set()
    for raw in roots:
        try:
            path = raw.expanduser().resolve()
        except OSError:
            continue
        if path in seen or not path.is_dir():
            continue
        # Nunca salir a raíces de sistema
        if not _is_windows(platform):
            parts = path.parts
            if parts[:1] == ("/",) and len(parts) >= 2 and parts[1] in {
                "usr",
                "etc",
                "var",
                "boot",
                "opt",
                "root",
                "sys",
                "proc",
                "dev",
            }:
                # Permitir solo si está bajo home
                try:
                    path.relative_to(home)
                except ValueError:
                    continue
        seen.add(path)
        unique.append(path)
    return unique


def find_candidates(
    root: Path,
    *,
    platform: str | None = None,
    scan_root: Path | None = None,
) -> list[TrashCandidate]:
    """Busca candidatos de basura de forma recursiva bajo `root`."""
    if not root.is_dir():
        return []

    found: list[TrashCandidate] = []
    root = root.resolve()
    label_root = (scan_root or root).resolve()

    for dirpath, dirnames, filenames in _walk_safe(root):
        dirnames[:] = [
            name
            for name in dirnames
            if not (Path(dirpath) / name).is_symlink()
        ]
        for filename in filenames:
            item = Path(dirpath) / filename
            if item.is_symlink():
                continue
            try:
                if not item.is_file():
                    continue
                size = item.stat().st_size
            except OSError:
                continue
            reason = _candidate_reason(item, size, platform=platform)
            if reason:
                found.append(
                    TrashCandidate(path=item, size=size, reason=reason, root=label_root)
                )

    found.sort(key=lambda c: str(c.path).lower())
    return found


def find_system_candidates(*, platform: str | None = None) -> list[TrashCandidate]:
    """Basura en temps/caché del usuario (varias raíces)."""
    found: list[TrashCandidate] = []
    seen_paths: set[Path] = set()
    for root in default_clean_roots(platform=platform):
        for candidate in find_candidates(root, platform=platform, scan_root=root):
            key = candidate.path
            if key in seen_paths:
                continue
            seen_paths.add(key)
            found.append(candidate)
    found.sort(key=lambda c: str(c.path).lower())
    return found


def _walk_safe(root: Path):
    try:
        yield from os.walk(root, followlinks=False)
    except OSError:
        return


def sort_candidates(
    candidates: list[TrashCandidate],
    key: str = "name",
    *,
    reverse: bool = False,
) -> list[TrashCandidate]:
    """Ordena candidatos por name|size|extension|reason."""
    if key not in _SORT_KEYS:
        key = "name"

    def sort_key(c: TrashCandidate):
        if key == "size":
            return c.size
        if key == "extension":
            return c.extension.lower()
        if key == "reason":
            return c.reason.casefold()
        return c.path.name.casefold()

    return sorted(candidates, key=sort_key, reverse=reverse)


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
