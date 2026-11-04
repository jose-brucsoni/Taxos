"""Registro append-only de acciones Taxos."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platformdirs import user_data_path

from taxos.cleaner import TrashCandidate
from taxos.organizer import MoveAction


def history_file() -> Path:
    return user_data_path("taxos") / "history.jsonl"


def _append_records(records: list[dict[str, Any]]) -> Path:
    path = history_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_moves(actions: list[MoveAction]) -> Path:
    """Añade una línea JSON por movimiento."""
    now = _now()
    records = [
        {
            "timestamp": now,
            "action": "move",
            "src": str(action.src),
            "dest": str(action.dest),
        }
        for action in actions
    ]
    return _append_records(records)


def append_organize_batch(
    actions: list[MoveAction],
    created_dirs: list[Path] | None = None,
    *,
    tags_path: Path | None = None,
    tags_previous: str | None = None,
    tags_written: bool = False,
    tag_count: int = 0,
    root: Path | str | None = None,
    method: str | None = None,
) -> Path:
    """Registra resumen del lote, carpetas creadas, movimientos y etiquetas."""
    now = _now()
    records: list[dict[str, Any]] = []

    root_str = str(root) if root else ""
    if not root_str and actions:
        root_str = str(actions[0].src.parent)
    if not root_str and tags_path is not None:
        root_str = str(Path(tags_path).parent)

    file_count = len(actions) + (tag_count if tags_written else 0)
    records.append(
        {
            "timestamp": now,
            "action": "batch",
            "kind": "organize",
            "root": root_str,
            "file_count": file_count,
            "method": method or "",
        }
    )

    for directory in created_dirs or []:
        records.append(
            {
                "timestamp": now,
                "action": "mkdir",
                "path": str(directory),
            }
        )
    for action in actions:
        records.append(
            {
                "timestamp": now,
                "action": "move",
                "src": str(action.src),
                "dest": str(action.dest),
            }
        )
    if tags_written and tags_path is not None:
        records.append(
            {
                "timestamp": now,
                "action": "tags",
                "path": str(tags_path),
                "previous": tags_previous,
            }
        )
    if len(records) == 1 and file_count == 0:
        return history_file()
    return _append_records(records)


def append_trash(
    candidates: list[TrashCandidate],
    *,
    root: Path | str | None = None,
) -> Path:
    """Añade resumen del lote y una línea JSON por archivo enviado a papelera."""
    now = _now()
    root_str = str(root) if root else ""
    if not root_str and candidates:
        root_str = str(candidates[0].path.parent)
    records: list[dict[str, Any]] = [
        {
            "timestamp": now,
            "action": "batch",
            "kind": "clean",
            "root": root_str,
            "file_count": len(candidates),
            "method": "",
        }
    ]
    records.extend(
        {
            "timestamp": now,
            "action": "trash",
            "src": str(candidate.path),
            "reason": candidate.reason,
        }
        for candidate in candidates
    )
    return _append_records(records)


def append_undos(
    actions: list[MoveAction],
    *,
    batch_timestamp: str | None = None,
) -> Path:
    """Añade deshacer (dest→src) y, si aplica, marca el lote como deshecho."""
    now = _now()
    records: list[dict[str, Any]] = []
    if batch_timestamp:
        records.append(
            {
                "timestamp": now,
                "action": "batch_undone",
                "undone_timestamp": batch_timestamp,
            }
        )
    records.extend(
        {
            "timestamp": now,
            "action": "undo",
            "src": str(action.src),
            "dest": str(action.dest),
        }
        for action in actions
    )
    if not records:
        return history_file()
    return _append_records(records)


def read_records() -> list[dict[str, Any]]:
    """Lee todo el historial; ignora líneas corruptas."""
    path = history_file()
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def last_move_batch() -> list[dict[str, Any]]:
    """Último lote de movimientos con el mismo timestamp."""
    moves = [r for r in read_records() if r.get("action") == "move"]
    if not moves:
        return []
    last_ts = moves[-1].get("timestamp")
    batch: list[dict[str, Any]] = []
    for record in reversed(moves):
        if record.get("timestamp") != last_ts:
            break
        batch.append(record)
    batch.reverse()
    return batch


def last_reversible_batch() -> list[dict[str, Any]]:
    """Último lote que se puede deshacer: movimientos y/o etiquetas, con sus mkdir."""
    records = read_records()
    undone = {
        record.get("undone_timestamp")
        for record in records
        if record.get("action") == "batch_undone" and record.get("undone_timestamp")
    }
    last_ts = None
    for record in reversed(records):
        if record.get("action") not in {"move", "tags"}:
            continue
        ts = record.get("timestamp")
        if ts in undone:
            continue
        last_ts = ts
        break
    if last_ts is None:
        return []
    return reversible_batch_at(last_ts)


def reversible_batch_at(timestamp: str) -> list[dict[str, Any]]:
    """Registros revertibles (move/mkdir/tags) de un timestamp concreto."""
    if not timestamp:
        return []
    return [
        record
        for record in read_records()
        if record.get("timestamp") == timestamp
        and record.get("action") in {"move", "mkdir", "tags"}
    ]


def _undone_timestamps(records: list[dict[str, Any]]) -> set[str]:
    return {
        str(record.get("undone_timestamp"))
        for record in records
        if record.get("action") == "batch_undone" and record.get("undone_timestamp")
    }


def list_history_batches() -> list[dict[str, Any]]:
    """Lotes de historial (más reciente primero): organize y clean."""
    from taxos.undo import summarize_batch

    records = read_records()
    undone = _undone_timestamps(records)
    explicit = [record for record in records if record.get("action") == "batch"]

    if explicit:
        batches: list[dict[str, Any]] = []
        for record in reversed(explicit):
            ts = str(record.get("timestamp") or "")
            kind = str(record.get("kind") or "organize")
            can_undo = False
            if kind == "organize" and ts and ts not in undone:
                can_undo = summarize_batch(reversible_batch_at(ts)).available
            batches.append(
                {
                    "timestamp": ts,
                    "kind": kind,
                    "root": str(record.get("root") or ""),
                    "file_count": int(record.get("file_count") or 0),
                    "method": str(record.get("method") or ""),
                    "can_undo": can_undo,
                }
            )
        return batches

    # Compatibilidad con historial antiguo sin action=batch
    return _legacy_history_batches(records, undone)


def _legacy_history_batches(
    records: list[dict[str, Any]],
    undone: set[str],
) -> list[dict[str, Any]]:
    from taxos.undo import summarize_batch

    seen: set[str] = set()
    batches: list[dict[str, Any]] = []
    for record in reversed(records):
        action = record.get("action")
        ts = str(record.get("timestamp") or "")
        if not ts or ts in seen:
            continue
        if action in {"move", "tags", "mkdir"}:
            seen.add(ts)
            batch = reversible_batch_at(ts)
            moves = [r for r in batch if r.get("action") == "move"]
            tags = [r for r in batch if r.get("action") == "tags"]
            root = ""
            if moves:
                root = str(Path(str(moves[0].get("src", ""))).parent)
            elif tags:
                root = str(Path(str(tags[0].get("path", ""))).parent)
            can_undo = ts not in undone and summarize_batch(batch).available
            batches.append(
                {
                    "timestamp": ts,
                    "kind": "organize",
                    "root": root,
                    "file_count": len(moves) + len(tags),
                    "method": "",
                    "can_undo": can_undo,
                }
            )
        elif action == "trash":
            seen.add(ts)
            trash = [r for r in records if r.get("timestamp") == ts and r.get("action") == "trash"]
            root = ""
            if trash:
                root = str(Path(str(trash[0].get("src", ""))).parent)
            batches.append(
                {
                    "timestamp": ts,
                    "kind": "clean",
                    "root": root,
                    "file_count": len(trash),
                    "method": "",
                    "can_undo": False,
                }
            )
    return batches
