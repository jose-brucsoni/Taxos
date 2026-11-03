"""Escaneo de archivos en una carpeta."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileEntry:
    path: Path
    size: int
    mtime: datetime

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def suffix(self) -> str:
        return self.path.suffix.lower()


def scan_dir(directory: Path) -> list[FileEntry]:
    """Lista solo archivos en la raíz de `directory` (sin subcarpetas)."""
    if not directory.is_dir():
        return []

    entries: list[FileEntry] = []
    for item in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_file():
            continue
        try:
            stat = item.stat()
        except OSError:
            continue
        entries.append(
            FileEntry(
                path=item,
                size=stat.st_size,
                mtime=datetime.fromtimestamp(stat.st_mtime),
            )
        )
    return entries
