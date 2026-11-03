"""Clasificación de archivos por extensión."""

from taxos.config import extension_index
from taxos.scanner import FileEntry


def classify(entry: FileEntry, rules: dict[str, list[str]]) -> str:
    """Devuelve la categoría del archivo; desconocidos → other."""
    index = extension_index(rules)
    return index.get(entry.suffix, "other")


def classify_all(
    entries: list[FileEntry], rules: dict[str, list[str]]
) -> list[tuple[FileEntry, str]]:
    """Clasifica una lista de entradas (índice de reglas una sola vez)."""
    index = extension_index(rules)
    return [(entry, index.get(entry.suffix, "other")) for entry in entries]
