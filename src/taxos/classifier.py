"""Clasificación de archivos por extensión (e IA opcional)."""

from __future__ import annotations

from taxos.ai import get_api_key, suggest_categories
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


def classify_with_optional_ai(
    entries: list[FileEntry],
    rules: dict[str, list[str]],
    *,
    use_ai: bool = False,
) -> tuple[list[tuple[FileEntry, str]], str | None]:
    """Clasifica localmente; si use_ai, mezcla sugerencias por nombre.

    Devuelve (clasificados, aviso_opcional).
    """
    local = classify_all(entries, rules)
    if not use_ai:
        return local, None

    api_key = get_api_key()
    if not api_key:
        return local, "Sin GROQ_API_KEY: se usan solo reglas locales."

    names = [entry.name for entry, _ in local if not entry.name.startswith(".")]
    if not names:
        return local, None

    categories = list(rules.keys()) + ["other"]
    suggestions = suggest_categories(names, categories, api_key)
    if not suggestions:
        return local, "IA no disponible o sin respuesta: reglas locales."

    merged: list[tuple[FileEntry, str]] = []
    for entry, category in local:
        merged.append((entry, suggestions.get(entry.name, category)))
    return merged, f"IA aplicada a {len(suggestions)} nombre(s)."
