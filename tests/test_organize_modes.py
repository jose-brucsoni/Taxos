"""Planes de organización: extensión, fecha, nombre, proyectos, duplicados y etiquetas."""

from datetime import datetime
from pathlib import Path

import pytest

from taxos.organize_modes import (
    OrganizeError,
    OrganizeRequest,
    assign_tags,
    normalize_request,
    plan_moves,
)
from taxos.scanner import FileEntry


RULES = {"images": [".jpg"], "documents": [".txt"]}


def _entry(path: Path, when: datetime, size: int = 10) -> FileEntry:
    return FileEntry(path=path, size=size, mtime=when)


def _folders(root: Path, names: list[tuple[str, datetime]], request: OrganizeRequest):
    entries = [_entry(root / name, when) for name, when in names]
    actions = plan_moves(root, entries, RULES, request)
    return {action.src.name: action.dest.parent.name for action in actions}


def test_extension_uses_rules_and_skips_dotfiles(tmp_path: Path) -> None:
    when = datetime(2024, 1, 2, 3, 4)
    folders = _folders(
        tmp_path,
        [("foto.jpg", when), ("nota.txt", when), (".oculto.jpg", when)],
        OrganizeRequest(method="extension"),
    )
    assert folders == {"foto.jpg": "images", "nota.txt": "documents"}


def test_date_granularity(tmp_path: Path) -> None:
    when = datetime(2024, 5, 9, 15, 0)
    names = [("informe.pdf", when)]
    assert _folders(tmp_path, names, OrganizeRequest(method="date", date_granularity="year")) == {
        "informe.pdf": "2024"
    }
    assert _folders(tmp_path, names, OrganizeRequest(method="date", date_granularity="month")) == {
        "informe.pdf": "2024-05"
    }
    assert _folders(tmp_path, names, OrganizeRequest(method="date", date_granularity="day")) == {
        "informe.pdf": "2024-05-09"
    }


def test_name_uses_first_word_when_no_terms(tmp_path: Path) -> None:
    when = datetime(2024, 1, 1)
    folders = _folders(
        tmp_path,
        [("Informe_final.pdf", when), ("---.txt", when)],
        OrganizeRequest(method="name"),
    )
    assert folders["Informe_final.pdf"] == "Informe"
    assert folders["---.txt"] == "Otros"


def test_name_matches_terms_case_insensitive(tmp_path: Path) -> None:
    when = datetime(2024, 1, 1)
    folders = _folders(
        tmp_path,
        [("Factura_marzo.pdf", when), ("notas.txt", when)],
        OrganizeRequest(method="name", terms=("factura",)),
    )
    assert folders == {"Factura_marzo.pdf": "factura"}


def test_projects_group_by_name_longest_match(tmp_path: Path) -> None:
    when = datetime(2024, 6, 1)
    folders = _folders(
        tmp_path,
        [
            ("informe-taxos-final.pdf", when),
            ("app-tax.txt", when),
            ("myapp-notas.txt", when),
            ("suelto.txt", when),
            (".taxos-secreto.txt", when),
        ],
        OrganizeRequest(method="projects", terms=("tax", "Taxos", "app", "myapp")),
    )
    assert folders["informe-taxos-final.pdf"] == "Taxos"
    assert folders["app-tax.txt"] == "tax"
    assert folders["myapp-notas.txt"] == "myapp"
    assert "suelto.txt" not in folders
    assert ".taxos-secreto.txt" not in folders


def test_projects_keep_the_user_spelling(tmp_path: Path) -> None:
    when = datetime(2024, 6, 1)
    folders = _folders(
        tmp_path,
        [("NOTAS-alpha.txt", when)],
        OrganizeRequest(method="projects", terms=("Alpha",)),
    )
    assert folders == {"NOTAS-alpha.txt": "Alpha"}


def test_duplicates_keep_oldest_and_move_the_rest(tmp_path: Path) -> None:
    older = tmp_path / "original.txt"
    newer = tmp_path / "copia.txt"
    other = tmp_path / "unico.txt"
    older.write_text("mismo", encoding="utf-8")
    newer.write_text("mismo", encoding="utf-8")
    other.write_text("distinto", encoding="utf-8")
    entries = [
        FileEntry(older, older.stat().st_size, datetime(2020, 1, 1)),
        FileEntry(newer, newer.stat().st_size, datetime(2024, 1, 1)),
        FileEntry(other, other.stat().st_size, datetime(2023, 1, 1)),
    ]
    actions = plan_moves(tmp_path, entries, RULES, OrganizeRequest(method="duplicates"))
    moved = {action.src.name: action.dest.parent.name for action in actions}
    assert moved == {"copia.txt": "Duplicados"}


def test_tags_do_not_move_and_follow_extension(tmp_path: Path) -> None:
    when = datetime(2024, 1, 1)
    entries = [
        _entry(tmp_path / "foto.jpg", when),
        _entry(tmp_path / ".oculto.jpg", when),
    ]
    request = OrganizeRequest(method="tags")
    assert plan_moves(tmp_path, entries, RULES, request) == []
    assert assign_tags(entries, RULES) == {"foto.jpg": ["images"]}


def test_normalize_projects_and_coming_soon() -> None:
    request = normalize_request("projects", terms=" Taxos, taxos ; Informe ")
    assert request.terms == ("Taxos", "Informe")
    date_request = normalize_request("date", granularity="día")
    assert date_request.date_granularity == "day"
    with pytest.raises(OrganizeError, match="proyecto"):
        normalize_request("projects", terms="  ")
    with pytest.raises(OrganizeError, match="próximamente"):
        normalize_request("content")
    with pytest.raises(OrganizeError, match="próximamente"):
        normalize_request("rules")
