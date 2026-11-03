"""Deshacer: ruta original, conflictos, carpetas vacías e historial."""

from datetime import datetime
from pathlib import Path

from taxos.history import append_organize_batch, last_reversible_batch
from taxos.organize_modes import OrganizeRequest, plan_moves, tags_path, write_tags
from taxos.organizer import apply_plan
from taxos.scanner import FileEntry
from taxos.undo import execute_undo, summarize_batch


def _write(path: Path, text: str, when: datetime | None = None) -> FileEntry:
    path.write_text(text, encoding="utf-8")
    return FileEntry(path, path.stat().st_size, when or datetime(2024, 3, 1))


def test_undo_restores_original_path_and_removes_empty_dir(tmp_path: Path) -> None:
    source = _write(tmp_path / "nota.txt", "hola")
    actions = plan_moves(
        tmp_path,
        [source],
        {"documents": [".txt"]},
        OrganizeRequest(method="extension"),
    )
    created: list[Path] = []
    done = apply_plan(actions, created)
    assert (tmp_path / "documents" / "nota.txt").is_file()
    assert not source.path.exists()
    assert created == [tmp_path / "documents"]

    summary = summarize_batch(
        [{"action": "move", "src": str(item.src), "dest": str(item.dest)} for item in done]
        + [{"action": "mkdir", "path": str(directory)} for directory in created]
    )
    outcome = execute_undo(summary)
    assert outcome.restored[0].dest == source.path
    assert outcome.restored[0].conflict is False
    assert source.path.read_text(encoding="utf-8") == "hola"
    assert not (tmp_path / "documents").exists()
    assert outcome.removed_dirs == [tmp_path / "documents"]


def test_undo_uses_another_name_when_original_is_taken(tmp_path: Path) -> None:
    source = _write(tmp_path / "nota.txt", "original")
    actions = plan_moves(
        tmp_path,
        [source],
        {"documents": [".txt"]},
        OrganizeRequest(method="extension"),
    )
    created: list[Path] = []
    done = apply_plan(actions, created)
    source.path.write_text("ocupado", encoding="utf-8")

    summary = summarize_batch(
        [{"action": "move", "src": str(item.src), "dest": str(item.dest)} for item in done]
        + [{"action": "mkdir", "path": str(directory)} for directory in created]
    )
    assert summary.actions[0].conflict is True
    outcome = execute_undo(summary)
    assert (tmp_path / "nota.txt").read_text(encoding="utf-8") == "ocupado"
    assert (tmp_path / "nota_1.txt").read_text(encoding="utf-8") == "original"
    assert outcome.restored[0].conflict is True
    assert not (tmp_path / "documents").exists()


def test_undo_skips_missing_destination(tmp_path: Path) -> None:
    source = _write(tmp_path / "nota.txt", "hola")
    actions = plan_moves(
        tmp_path,
        [source],
        {"documents": [".txt"]},
        OrganizeRequest(method="extension"),
    )
    done = apply_plan(actions, [])
    done[0].dest.unlink()
    summary = summarize_batch(
        [{"action": "move", "src": str(item.src), "dest": str(item.dest)} for item in done]
    )
    assert summary.actions == []
    outcome = execute_undo(summary)
    assert outcome.restored == []


def test_undo_keeps_preexisting_and_non_empty_dirs(tmp_path: Path) -> None:
    preexisting = tmp_path / "documents"
    preexisting.mkdir()
    (preexisting / "viejo.txt").write_text("quedo", encoding="utf-8")
    source = _write(tmp_path / "nota.txt", "nueva")
    actions = plan_moves(
        tmp_path,
        [source],
        {"documents": [".txt"]},
        OrganizeRequest(method="extension"),
    )
    created: list[Path] = []
    done = apply_plan(actions, created)
    assert created == []

    summary = summarize_batch(
        [{"action": "move", "src": str(item.src), "dest": str(item.dest)} for item in done]
    )
    execute_undo(summary)
    assert (tmp_path / "nota.txt").is_file()
    assert (preexisting / "viejo.txt").is_file()
    assert preexisting.is_dir()


def test_undo_does_not_remove_created_dir_that_still_has_files(tmp_path: Path) -> None:
    first = _write(tmp_path / "a.txt", "a")
    second = _write(tmp_path / "b.txt", "b")
    actions = plan_moves(
        tmp_path,
        [first, second],
        {"documents": [".txt"]},
        OrganizeRequest(method="extension"),
    )
    created: list[Path] = []
    done = apply_plan(actions, created)
    kept = next(item for item in done if item.src.name == "b.txt")
    summary = summarize_batch(
        [
            {"action": "move", "src": str(item.src), "dest": str(item.dest)}
            for item in done
            if item.src.name == "a.txt"
        ]
        + [{"action": "mkdir", "path": str(directory)} for directory in created]
    )
    outcome = execute_undo(summary)
    assert (tmp_path / "a.txt").is_file()
    assert kept.dest.is_file()
    assert (tmp_path / "documents").is_dir()
    assert outcome.removed_dirs == []


def test_undo_removes_empty_created_dir_when_file_is_gone(tmp_path: Path) -> None:
    folder = tmp_path / "Docs"
    folder.mkdir()
    batch = [
        {"action": "mkdir", "path": str(folder), "timestamp": "t"},
        {
            "action": "move",
            "src": str(tmp_path / "a.txt"),
            "dest": str(folder / "a.txt"),
            "timestamp": "t",
        },
    ]
    summary = summarize_batch(batch)
    assert summary.actions == []
    assert summary.available is True
    outcome = execute_undo(summary)
    assert not folder.exists()
    assert outcome.removed_dirs == [folder]


def test_history_batch_groups_mkdir_and_move(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "history.jsonl"
    monkeypatch.setattr("taxos.history.history_file", lambda: log)
    source = tmp_path / "nota.txt"
    dest = tmp_path / "documents" / "nota.txt"
    from taxos.organizer import MoveAction

    append_organize_batch(
        [MoveAction(src=source, dest=dest)],
        [tmp_path / "documents"],
    )
    batch = last_reversible_batch()
    kinds = [record["action"] for record in batch]
    assert kinds == ["mkdir", "move"]
    assert batch[0]["timestamp"] == batch[1]["timestamp"]


def test_undo_restores_or_removes_tags_file(tmp_path: Path) -> None:
    path = tags_path(tmp_path)
    write_tags(path, {"a.txt": ["documents"]})
    created = path.read_text(encoding="utf-8")
    outcome = execute_undo(
        summarize_batch(
            [{"action": "tags", "path": str(path), "previous": None, "timestamp": "t"}]
        )
    )
    assert outcome.tags_restored == 1
    assert not path.exists()

    path.write_text(created, encoding="utf-8")
    execute_undo(
        summarize_batch(
            [
                {
                    "action": "tags",
                    "path": str(path),
                    "previous": '{"version": 0}\n',
                    "timestamp": "t",
                }
            ]
        )
    )
    assert path.read_text(encoding="utf-8") == '{"version": 0}\n'
