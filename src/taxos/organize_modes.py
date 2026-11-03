"""Modos de organización que usa el asistente (sin contenido ni reglas)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from taxos.classifier import classify_all
from taxos.organizer import MoveAction, build_plan
from taxos.scanner import FileEntry

ENABLED_METHODS = frozenset(
    {"extension", "date", "name", "tags", "duplicates", "projects"}
)
COMING_SOON_METHODS = frozenset({"content", "rules"})

DUPLICATES_FOLDER = "Duplicados"
OTHER_NAME_FOLDER = "Otros"
TAGS_FILENAME = ".taxos-etiquetas.json"

_GRANULARITY = {
    "year": "year",
    "año": "year",
    "ano": "year",
    "month": "month",
    "mes": "month",
    "day": "day",
    "día": "day",
    "dia": "day",
}

_WORD = re.compile(r"[0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")
_TERM_SPLIT = re.compile(r"[,;\n]+")


class OrganizeError(ValueError):
    """Petición de organización que no se puede aplicar."""


@dataclass(frozen=True)
class OrganizeRequest:
    method: str = "extension"
    date_granularity: str = "month"
    terms: tuple[str, ...] = ()


def sanitize_label(label: str) -> str:
    """Convierte un texto del usuario en un nombre de carpeta de un solo nivel."""
    cleaned = " ".join(label.strip().split())
    for char in ("/", "\\", ":", "\0"):
        cleaned = cleaned.replace(char, "-")
    cleaned = cleaned.strip(" .")
    if not cleaned or cleaned in {".", ".."} or any(char in cleaned for char in '<>|"?*'):
        raise OrganizeError(f"Nombre de carpeta no válido: {label.strip()}")
    return cleaned


def parse_terms(text: str) -> tuple[str, ...]:
    """Separa nombres por coma, punto y coma o salto de línea, sin duplicados."""
    terms: list[str] = []
    seen: set[str] = set()
    for part in _TERM_SPLIT.split(text or ""):
        if not part.strip():
            continue
        label = sanitize_label(part)
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        terms.append(label)
    return tuple(terms)


def normalize_request(
    method: str,
    *,
    granularity: str = "month",
    terms: str = "",
) -> OrganizeRequest:
    """Valida el modo elegido en la interfaz."""
    key = (method or "").strip().lower()
    if key in COMING_SOON_METHODS:
        raise OrganizeError("Ese modo estará disponible próximamente.")
    if key not in ENABLED_METHODS:
        raise OrganizeError("Modo de organización desconocido.")

    raw_granularity = (granularity or "month").strip().lower()
    mapped = _GRANULARITY.get(raw_granularity)
    if key == "date" and mapped is None:
        raise OrganizeError("Elige año, mes o día.")

    parsed = parse_terms(terms)
    if key == "projects" and not parsed:
        raise OrganizeError("Indica al menos un nombre de proyecto.")
    return OrganizeRequest(
        method=key,
        date_granularity=mapped or "month",
        terms=parsed,
    )


def _visible(entries: list[FileEntry]) -> list[FileEntry]:
    return [entry for entry in entries if not entry.name.startswith(".")]


def _date_folder(moment: datetime, granularity: str) -> str:
    if granularity == "year":
        return f"{moment.year:04d}"
    if granularity == "day":
        return f"{moment:%Y-%m-%d}"
    return f"{moment:%Y-%m}"


def _match_term(name: str, terms: tuple[str, ...]) -> str | None:
    """Coincidencia más larga, sin distinguir mayúsculas. Empate: orden del usuario."""
    folded = name.casefold()
    found = [term for term in terms if term.casefold() in folded]
    if not found:
        return None
    found.sort(key=lambda term: (-len(term.casefold()), terms.index(term)))
    return found[0]


def _first_word(filename: str) -> str | None:
    match = _WORD.search(Path(filename).stem)
    if match is None:
        return None
    return match.group(0)


def _assign_name(entries: list[FileEntry], terms: tuple[str, ...]) -> list[tuple[FileEntry, str]]:
    assigned: list[tuple[FileEntry, str]] = []
    for entry in _visible(entries):
        if terms:
            folder = _match_term(entry.name, terms)
            if folder is None:
                continue
        else:
            folder = _first_word(entry.name) or OTHER_NAME_FOLDER
        assigned.append((entry, folder))
    return assigned


def _assign_projects(
    entries: list[FileEntry], terms: tuple[str, ...]
) -> list[tuple[FileEntry, str]]:
    assigned: list[tuple[FileEntry, str]] = []
    for entry in _visible(entries):
        folder = _match_term(entry.name, terms)
        if folder is None:
            continue
        assigned.append((entry, folder))
    return assigned


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assign_duplicates(entries: list[FileEntry]) -> list[tuple[FileEntry, str]]:
    """Conserva la copia más antigua y aparta el resto en Duplicados."""
    by_size: dict[int, list[FileEntry]] = {}
    for entry in _visible(entries):
        if not entry.path.is_file():
            continue
        by_size.setdefault(entry.size, []).append(entry)

    assigned: list[tuple[FileEntry, str]] = []
    for group in by_size.values():
        if len(group) < 2:
            continue
        hashed: dict[str, list[FileEntry]] = {}
        for entry in group:
            try:
                digest = _sha256(entry.path)
            except OSError:
                continue
            hashed.setdefault(digest, []).append(entry)
        for same in hashed.values():
            if len(same) < 2:
                continue
            ordered = sorted(same, key=lambda item: (item.mtime, item.name.casefold()))
            for extra in ordered[1:]:
                assigned.append((extra, DUPLICATES_FOLDER))
    return assigned


def assign_folders(
    entries: list[FileEntry],
    rules: dict[str, list[str]],
    request: OrganizeRequest,
) -> list[tuple[FileEntry, str]]:
    """Carpeta de un nivel para cada archivo que sí se mueve."""
    if request.method == "tags":
        return []
    if request.method == "extension":
        return [
            (entry, category)
            for entry, category in classify_all(entries, rules)
            if not entry.name.startswith(".")
        ]
    if request.method == "date":
        return [
            (entry, _date_folder(entry.mtime, request.date_granularity))
            for entry in _visible(entries)
        ]
    if request.method == "name":
        return _assign_name(entries, request.terms)
    if request.method == "projects":
        return _assign_projects(entries, request.terms)
    if request.method == "duplicates":
        return _assign_duplicates(entries)
    raise OrganizeError("Modo de organización desconocido.")


def plan_moves(
    root: Path,
    entries: list[FileEntry],
    rules: dict[str, list[str]],
    request: OrganizeRequest,
) -> list[MoveAction]:
    """Plan de movimientos. El modo etiquetas no mueve archivos."""
    return build_plan(root, assign_folders(entries, rules, request))


def assign_tags(
    entries: list[FileEntry],
    rules: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Etiqueta por categoría de extensión, sin mover el archivo."""
    tags: dict[str, list[str]] = {}
    for entry, category in classify_all(entries, rules):
        if entry.name.startswith("."):
            continue
        tags[entry.name] = [category]
    return tags


def tags_path(root: Path) -> Path:
    return root / TAGS_FILENAME


def read_tags_raw(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def write_tags(path: Path, mapping: dict[str, list[str]]) -> None:
    payload = {"version": 1, "files": mapping}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def restore_tags(path: Path, previous: str | None) -> bool:
    """Vuelve al contenido anterior o borra el archivo si no existía."""
    try:
        if previous is None:
            if path.is_file():
                path.unlink()
            return True
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(previous, encoding="utf-8")
        return True
    except OSError:
        return False
