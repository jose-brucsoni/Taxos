"""Tests de búsqueda por nombre/extensión."""

from __future__ import annotations

from pathlib import Path

from taxos.search import search_files


def test_search_by_name_and_ext(tmp_path: Path) -> None:
    (tmp_path / "InformeFinal.pdf").write_bytes(b"a")
    (tmp_path / "foto.png").write_bytes(b"b")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "informe-borrador.pdf").write_bytes(b"c")

    hits = search_files(tmp_path, name_query="informe", extension="pdf")
    names = {h.name for h in hits}
    assert names == {"InformeFinal.pdf", "informe-borrador.pdf"}


def test_search_requires_query_or_ext(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    assert search_files(tmp_path) == []


def test_search_skips_node_modules(tmp_path: Path) -> None:
    nested = tmp_path / "node_modules" / "pkg"
    nested.mkdir(parents=True)
    (nested / "secret.pdf").write_bytes(b"x")
    (tmp_path / "visible.pdf").write_bytes(b"y")
    hits = search_files(tmp_path, extension="pdf")
    assert [h.name for h in hits] == ["visible.pdf"]


def test_search_limit(tmp_path: Path) -> None:
    for i in range(10):
        (tmp_path / f"file{i}.txt").write_bytes(b"z")
    hits = search_files(tmp_path, extension="txt", limit=3)
    assert len(hits) == 3
