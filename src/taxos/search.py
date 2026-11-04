"""Búsqueda de archivos por nombre y/o extensión en el perfil de usuario."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_LIMIT = 500

# Carpetas a no entrar cuando se busca en el home del usuario.
_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        ".cache",
        ".local",
        ".npm",
        ".cargo",
        ".rustup",
        ".pyenv",
        "AppData",  # Windows: muy grande; el usuario puede buscar carpeta concreta
        "Application Data",
        "Cookies",
        "Recent",
    }
)


@dataclass(frozen=True)
class SearchHit:
    path: Path
    size: int

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def extension(self) -> str:
        suffix = self.path.suffix.lower()
        return suffix[1:] if suffix.startswith(".") else suffix

    @property
    def parent(self) -> Path:
        return self.path.parent


def normalize_extension(ext: str | None) -> str | None:
    if ext is None:
        return None
    cleaned = ext.strip().lstrip(".").casefold()
    return cleaned or None


def user_search_root() -> Path:
    """Raíz de “Buscar en toda la PC”: perfil del usuario."""
    return Path.home().resolve()


def search_files(
    root: Path,
    *,
    name_query: str = "",
    extension: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[SearchHit]:
    """Busca archivos bajo `root` por substring en el nombre y/o extensión."""
    if not root.is_dir():
        return []

    query = (name_query or "").strip().casefold()
    ext = normalize_extension(extension)
    if not query and not ext:
        return []

    root = root.resolve()
    hits: list[SearchHit] = []
    limit = max(1, int(limit))

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in _SKIP_DIR_NAMES and not (Path(dirpath) / name).is_symlink()
        ]
        for filename in filenames:
            if len(hits) >= limit:
                return hits
            path = Path(dirpath) / filename
            if path.is_symlink():
                continue
            try:
                if not path.is_file():
                    continue
            except OSError:
                continue

            name_cf = filename.casefold()
            file_ext = path.suffix.lower().lstrip(".")
            if query and query not in name_cf:
                continue
            if ext and file_ext != ext:
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            hits.append(SearchHit(path=path, size=size))

    return hits
