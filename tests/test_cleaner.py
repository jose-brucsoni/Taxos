"""Tests del cleaner recursivo y reglas por SO."""

from __future__ import annotations

from pathlib import Path

import pytest

from taxos.cleaner import (
    default_clean_roots,
    find_candidates,
    find_system_candidates,
    sort_candidates,
)


def _touch(path: Path, size: int = 10) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_recursive_and_empty(tmp_path: Path) -> None:
    _touch(tmp_path / "ok.pdf", 100)
    _touch(tmp_path / "sub" / "vacio.txt", 0)
    _touch(tmp_path / "sub" / "a.tmp", 20)
    found = find_candidates(tmp_path, platform="linux")
    names = {c.path.name for c in found}
    assert names == {"vacio.txt", "a.tmp"}
    empty = next(c for c in found if c.path.name == "vacio.txt")
    assert empty.reason == "vacío"


def test_linux_rules(tmp_path: Path) -> None:
    _touch(tmp_path / "notes.txt~")
    _touch(tmp_path / ".foo.swp")
    _touch(tmp_path / ".DS_Store")
    _touch(tmp_path / ".fuse_hidden123")
    _touch(tmp_path / "keep.txt")
    found = find_candidates(tmp_path, platform="linux")
    names = {c.path.name for c in found}
    assert "notes.txt~" in names
    assert ".foo.swp" in names
    assert ".DS_Store" in names
    assert ".fuse_hidden123" in names
    assert "keep.txt" not in names


def test_windows_rules(tmp_path: Path) -> None:
    _touch(tmp_path / "Thumbs.db")
    _touch(tmp_path / "desktop.ini")
    _touch(tmp_path / "~$doc.docx")
    _touch(tmp_path / "crash.stackdump")
    _touch(tmp_path / "photo.jpg")
    found = find_candidates(tmp_path, platform="win32")
    names = {c.path.name for c in found}
    assert names == {"Thumbs.db", "desktop.ini", "~$doc.docx", "crash.stackdump"}


def test_windows_rules_not_on_linux(tmp_path: Path) -> None:
    _touch(tmp_path / "Thumbs.db")
    found = find_candidates(tmp_path, platform="linux")
    assert found == []


def test_sort_candidates(tmp_path: Path) -> None:
    _touch(tmp_path / "b.tmp", 30)
    _touch(tmp_path / "a.tmp", 10)
    found = find_candidates(tmp_path, platform="linux")
    by_size = sort_candidates(found, "size")
    assert [c.size for c in by_size] == [10, 30]
    by_name = sort_candidates(found, "name", reverse=True)
    assert [c.path.name for c in by_name] == ["b.tmp", "a.tmp"]


def test_default_clean_roots_linux_uses_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / ".cache"
    cache.mkdir()
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr("taxos.cleaner.tempfile.gettempdir", lambda: str(tmp_path / "not-temp"))
    roots = default_clean_roots(platform="linux")
    assert cache.resolve() in roots
    assert all(str(r).startswith(str(tmp_path)) for r in roots)


def test_find_system_candidates_scans_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / ".cache"
    _touch(cache / "x.tmp", 20)
    _touch(cache / "keep.pdf", 20)
    monkeypatch.setattr(
        "taxos.cleaner.default_clean_roots",
        lambda platform=None: [cache.resolve()],
    )
    found = find_system_candidates(platform="linux")
    assert {c.path.name for c in found} == {"x.tmp"}
    assert found[0].root == cache.resolve()
