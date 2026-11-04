"""Tests de preferencias GUI (merge y flags de onboarding)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from taxos.gui import prefs as prefs_mod


@pytest.fixture()
def prefs_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "gui.json"
    monkeypatch.setattr(prefs_mod, "_prefs_path", lambda: path)
    return path


def test_defaults_when_missing(prefs_file: Path) -> None:
    assert not prefs_file.is_file()
    data = prefs_mod.load_gui_prefs()
    assert data == {
        "appearance_mode": "Light",
        "tutorial_seen": False,
        "preview_tip_seen": False,
        "undo_tip_seen": False,
    }


def test_merge_preserves_flags(prefs_file: Path) -> None:
    prefs_mod.save_gui_prefs({"tutorial_seen": True, "preview_tip_seen": True})
    prefs_mod.save_gui_prefs({"appearance_mode": "Dark"})
    data = prefs_mod.load_gui_prefs()
    assert data["appearance_mode"] == "Dark"
    assert data["tutorial_seen"] is True
    assert data["preview_tip_seen"] is True
    assert data["undo_tip_seen"] is False


def test_invalid_bools_fall_back(prefs_file: Path) -> None:
    prefs_file.write_text(
        json.dumps(
            {
                "appearance_mode": "Light",
                "tutorial_seen": "yes",
                "preview_tip_seen": 1,
                "undo_tip_seen": None,
            }
        ),
        encoding="utf-8",
    )
    data = prefs_mod.load_gui_prefs()
    assert data["tutorial_seen"] is False
    assert data["preview_tip_seen"] is False
    assert data["undo_tip_seen"] is False


def test_invalid_mode_falls_back(prefs_file: Path) -> None:
    prefs_file.write_text(json.dumps({"appearance_mode": "Neon"}), encoding="utf-8")
    assert prefs_mod.load_gui_prefs()["appearance_mode"] == "Light"


def test_update_gui_prefs_partial(prefs_file: Path) -> None:
    out = prefs_mod.update_gui_prefs(tutorial_seen=True)
    assert out["tutorial_seen"] is True
    assert out["appearance_mode"] == "Light"
    assert prefs_mod.load_gui_prefs()["tutorial_seen"] is True


def test_update_gui_prefs_rejects_unknown(prefs_file: Path) -> None:
    with pytest.raises(ValueError, match="desconocidas"):
        prefs_mod.update_gui_prefs(foo=True)
