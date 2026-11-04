"""API expuesta a JavaScript vía PyWebView."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import webview

from taxos.cleaner import (
    TrashCandidate,
    apply_trash,
    default_clean_roots,
    find_system_candidates,
    sort_candidates,
)
from taxos.config import load_rules
from taxos.gui.prefs import ONBOARDING_FLAGS, load_gui_prefs, save_gui_prefs, update_gui_prefs
from taxos.search import search_files as run_search
from taxos.search import user_search_root
from taxos.history import (
    append_organize_batch,
    append_trash,
    append_undos,
    last_reversible_batch,
    list_history_batches,
    reversible_batch_at,
)
from taxos.organize_modes import (
    TAGS_FILENAME,
    OrganizeError,
    OrganizeRequest,
    assign_tags,
    normalize_request,
    plan_moves,
    read_tags_raw,
    tags_path,
    write_tags,
)
from taxos.organizer import MoveAction, apply_plan
from taxos.paths import get_downloads_dir
from taxos.scanner import scan_dir
from taxos.undo import UndoOutcome, UndoSummary, execute_undo, summarize_batch


def _has_groq_key() -> bool:
    return bool(os.environ.get("GROQ_API_KEY", "").strip())


def _format_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def _undo_payload(summary: UndoSummary) -> dict[str, Any]:
    lines: list[str] = []
    for action in summary.actions[:40]:
        note = " (otro nombre: la ruta original está ocupada)" if action.conflict else ""
        lines.append(f"{action.src.name} → {action.dest.name}{note}")
    if len(summary.actions) > 40:
        lines.append(f"… y {len(summary.actions) - 40} más")
    if summary.tags:
        lines.append("Se restaurará el archivo de etiquetas anterior.")
    if summary.cleanup_dirs and not summary.actions:
        lines.append("Se eliminarán carpetas creadas que quedaron vacías.")
    return {
        "available": summary.available,
        "move_count": len(summary.actions),
        "conflict_count": sum(1 for action in summary.actions if action.conflict),
        "tags": bool(summary.tags),
        "lines": lines,
    }


def _undo_message(outcome: UndoOutcome) -> str:
    conflicts = sum(1 for action in outcome.restored if action.conflict)
    parts = [f"Restaurados: {len(outcome.restored)}."]
    if conflicts:
        parts.append(f"Con otro nombre por conflicto: {conflicts}.")
    if outcome.removed_dirs:
        parts.append(f"Carpetas vacías eliminadas: {len(outcome.removed_dirs)}.")
    if outcome.tags_restored:
        parts.append("Etiquetas restauradas.")
    return " ".join(parts)


class TaxosApi:
    def __init__(self) -> None:
        self.target = get_downloads_dir()
        self.do_organize = True
        self.do_clean = False
        self.use_ai = False
        self.request = OrganizeRequest()
        self.move_actions: list[MoveAction] = []
        self.trash_candidates: list[TrashCandidate] = []
        self.selected_trash_paths: set[str] | None = None
        self.tag_mapping: dict[str, list[str]] = {}
        self.do_search = False

    def get_state(self) -> dict[str, Any]:
        prefs = load_gui_prefs()
        return {
            "folder": str(self.target),
            "theme": prefs.get("appearance_mode", "Light"),
            "has_groq_key": _has_groq_key(),
            "do_organize": self.do_organize,
            "do_clean": self.do_clean,
            "use_ai": self.use_ai,
            "tutorial_seen": bool(prefs.get("tutorial_seen")),
            "preview_tip_seen": bool(prefs.get("preview_tip_seen")),
            "undo_tip_seen": bool(prefs.get("undo_tip_seen")),
        }

    def set_theme(self, mode: str) -> dict[str, Any]:
        if mode not in {"System", "Light", "Dark"}:
            mode = "System"
        save_gui_prefs({"appearance_mode": mode})
        return {"ok": True, "theme": mode}

    def set_onboarding_flag(self, name: str, value: bool = True) -> dict[str, Any]:
        if name not in ONBOARDING_FLAGS:
            return {"ok": False, "error": "Flag de onboarding desconocido."}
        prefs = update_gui_prefs(**{name: bool(value)})
        return {"ok": True, "name": name, "value": bool(prefs.get(name))}

    def set_operation(self, kind: str) -> dict[str, Any]:
        self.do_search = False
        self.selected_trash_paths = None
        if kind == "organize":
            self.do_organize, self.do_clean = True, False
        elif kind == "clean":
            self.do_organize, self.do_clean = False, True
        elif kind == "search":
            self.do_organize, self.do_clean = False, False
            self.do_search = True
        else:
            return {"ok": False, "error": "Operación desconocida."}
        return {
            "ok": True,
            "do_organize": self.do_organize,
            "do_clean": self.do_clean,
            "do_search": self.do_search,
        }

    def set_folder(self, path: str) -> dict[str, Any]:
        candidate = Path(path)
        if not candidate.is_dir():
            return {"ok": False, "error": f"No existe la carpeta:\n{path}"}
        self.target = candidate
        return {"ok": True, "folder": str(self.target)}

    def browse_folder(self) -> str | None:
        window = webview.active_window()
        if window is None and webview.windows:
            window = webview.windows[0]
        if window is None:
            return None
        result = window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=str(self.target) if self.target.is_dir() else str(Path.home()),
        )
        if not result:
            return None
        chosen = result[0] if isinstance(result, (list, tuple)) else result
        path = Path(str(chosen))
        if path.is_dir():
            self.target = path
            return str(path)
        return None

    def set_organize_options(
        self,
        method: str,
        granularity: str = "month",
        terms: str = "",
    ) -> dict[str, Any]:
        try:
            self.request = normalize_request(
                method,
                granularity=granularity or "month",
                terms=terms or "",
            )
        except OrganizeError as exc:
            return {"ok": False, "error": str(exc)}
        return {
            "ok": True,
            "method": self.request.method,
            "granularity": self.request.date_granularity,
            "terms": list(self.request.terms),
        }

    def set_use_ai(self, enabled: bool) -> dict[str, Any]:
        if enabled and not _has_groq_key():
            return {
                "ok": False,
                "error": (
                    "No hay GROQ_API_KEY. Configúrala en el entorno o en un archivo .env, "
                    "o pulsa Omitir para usar las reglas locales."
                ),
            }
        self.use_ai = bool(enabled)
        return {"ok": True, "use_ai": self.use_ai}

    def build_preview(self) -> dict[str, Any]:
        self.move_actions = []
        self.trash_candidates = []
        self.tag_mapping = {}
        if not self.target.is_dir():
            return {
                "move_count": 0,
                "trash_count": 0,
                "groups": [],
                "lines": [f"No existe la carpeta:\n{self.target}"],
            }

        if self.do_organize:
            rules = load_rules()
            entries = scan_dir(self.target)
            if self.request.method == "tags":
                self.tag_mapping = assign_tags(entries, rules)
            else:
                try:
                    self.move_actions = plan_moves(
                        self.target, entries, rules, self.request
                    )
                except OrganizeError as exc:
                    return {
                        "move_count": 0,
                        "trash_count": 0,
                        "groups": [],
                        "lines": [str(exc)],
                        "error": str(exc),
                    }

        # La basura se gestiona solo con build_clean_preview / clean_select.
        self.trash_candidates = []

        groups: list[dict[str, Any]] = []
        folder_files: dict[str, list[dict[str, Any]]] = {}
        folder_totals: dict[str, list[int]] = {}
        for action in self.move_actions:
            name = action.dest.parent.name
            try:
                size = action.src.stat().st_size
            except OSError:
                size = 0
            bucket = folder_totals.setdefault(name, [0, 0])
            bucket[0] += 1
            bucket[1] += size
            folder_files.setdefault(name, []).append(
                {
                    "name": action.src.name,
                    "size_bytes": size,
                    "size_label": _format_size(size),
                }
            )

        for name in sorted(folder_totals.keys()):
            count, size_bytes = folder_totals[name]
            groups.append(
                {
                    "name": name,
                    "kind": "move",
                    "count": count,
                    "size_bytes": size_bytes,
                    "size_label": _format_size(size_bytes),
                    "files": folder_files.get(name, []),
                }
            )

        if self.tag_mapping:
            tag_groups: dict[str, list[dict[str, Any]]] = {}
            tag_totals: dict[str, list[int]] = {}
            for name, labels in self.tag_mapping.items():
                label = labels[0] if labels else "other"
                try:
                    size = (self.target / name).stat().st_size
                except OSError:
                    size = 0
                bucket = tag_totals.setdefault(label, [0, 0])
                bucket[0] += 1
                bucket[1] += size
                tag_groups.setdefault(label, []).append(
                    {
                        "name": name,
                        "size_bytes": size,
                        "size_label": _format_size(size),
                    }
                )
            for name in sorted(tag_totals.keys()):
                count, size_bytes = tag_totals[name]
                groups.append(
                    {
                        "name": name,
                        "kind": "tag",
                        "count": count,
                        "size_bytes": size_bytes,
                        "size_label": _format_size(size_bytes),
                        "files": tag_groups.get(name, []),
                    }
                )

        lines: list[str] = []
        if self.do_organize:
            for action in self.move_actions[:50]:
                try:
                    rel = action.dest.relative_to(self.target)
                except ValueError:
                    rel = action.dest
                lines.append(f"{action.src.name} → {rel}")
            if len(self.move_actions) > 50:
                lines.append(f"… y {len(self.move_actions) - 50} más")
            if self.tag_mapping:
                lines.append(
                    f"Etiquetas (sin mover): {len(self.tag_mapping)} archivo(s) "
                    f"en {TAGS_FILENAME}"
                )
        if not self.move_actions and not self.tag_mapping:
            lines.append("Nada que organizar en esta carpeta.")

        return {
            "move_count": len(self.move_actions),
            "trash_count": 0,
            "tag_count": len(self.tag_mapping),
            "groups": groups,
            "lines": lines,
        }

    def build_clean_preview(self, sort_by: str = "name", reverse: bool = False) -> dict[str, Any]:
        roots = default_clean_roots()
        self.trash_candidates = find_system_candidates()
        ordered = sort_candidates(self.trash_candidates, sort_by, reverse=bool(reverse))
        items: list[dict[str, Any]] = []
        for candidate in ordered:
            path_str = str(candidate.path)
            selected = (
                True
                if self.selected_trash_paths is None
                else path_str in self.selected_trash_paths
            )
            root_str = str(candidate.root) if candidate.root else ""
            items.append(
                {
                    "path": path_str,
                    "name": candidate.path.name,
                    "rel_path": candidate.relative_label(),
                    "root": root_str,
                    "extension": candidate.extension,
                    "size_bytes": candidate.size,
                    "size_label": _format_size(candidate.size),
                    "reason": candidate.reason,
                    "selected": selected,
                }
            )
        total_bytes = sum(c.size for c in ordered)
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "sort_by": sort_by,
            "reverse": bool(reverse),
            "roots": [str(r) for r in roots],
            "total_size_bytes": total_bytes,
            "total_size_label": _format_size(total_bytes),
        }

    def set_clean_selection(self, paths: list[str] | None = None) -> dict[str, Any]:
        if paths is None:
            self.selected_trash_paths = None
            return {"ok": True, "count": len(self.trash_candidates)}
        wanted = {str(p) for p in paths}
        self.selected_trash_paths = wanted
        return {"ok": True, "count": len(wanted)}

    def _selected_trash(self) -> list[TrashCandidate]:
        if self.selected_trash_paths is None:
            return list(self.trash_candidates)
        return [c for c in self.trash_candidates if str(c.path) in self.selected_trash_paths]

    def search_files(
        self,
        name: str = "",
        extension: str = "",
        scope: str = "folder",
        limit: int = 500,
    ) -> dict[str, Any]:
        if scope == "all_user":
            root = user_search_root()
        else:
            root = self.target
        if not root.is_dir():
            return {"ok": False, "error": f"No existe la carpeta:\n{root}", "hits": []}
        if not (name or "").strip() and not (extension or "").strip():
            return {
                "ok": False,
                "error": "Indica un texto de nombre y/o una extensión.",
                "hits": [],
            }
        hits = run_search(
            root,
            name_query=name or "",
            extension=extension or None,
            limit=int(limit) or 500,
        )
        return {
            "ok": True,
            "root": str(root),
            "truncated": len(hits) >= (int(limit) or 500),
            "hits": [
                {
                    "path": str(hit.path),
                    "name": hit.name,
                    "extension": hit.extension,
                    "parent": str(hit.parent),
                    "size_bytes": hit.size,
                    "size_label": _format_size(hit.size),
                }
                for hit in hits
            ],
        }

    def reveal_path(self, path: str) -> dict[str, Any]:
        target = Path(path)
        folder = target if target.is_dir() else target.parent
        if not folder.is_dir():
            return {"ok": False, "error": "No se pudo abrir la carpeta."}
        try:
            import os
            import subprocess

            if sys.platform.startswith("win"):
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "folder": str(folder)}

    def apply_plan(self) -> dict[str, Any]:
        if not self.do_organize and not self.do_clean:
            return {"ok": False, "error": "No hay operación seleccionada."}
        trash_to_apply = self._selected_trash() if self.do_clean else []
        if not self.move_actions and not trash_to_apply and not self.tag_mapping:
            return {"ok": False, "error": "No hay acciones en el plan."}

        moved = 0
        trashed = 0
        tagged = 0
        created: list[Path] = []
        done: list[MoveAction] = []
        tags_file = None
        tags_previous = None
        if self.move_actions:
            done = apply_plan(self.move_actions, created)
            moved = len(done)
        if self.tag_mapping:
            tags_file = tags_path(self.target)
            tags_previous = read_tags_raw(tags_file)
            write_tags(tags_file, self.tag_mapping)
            tagged = len(self.tag_mapping)
        if done or tagged:
            append_organize_batch(
                done,
                created,
                tags_path=tags_file,
                tags_previous=tags_previous,
                tags_written=bool(tagged),
                tag_count=tagged,
                root=self.target,
                method=self.request.method,
            )
        if trash_to_apply:
            done_trash = apply_trash(trash_to_apply)
            trash_root = (
                trash_to_apply[0].root
                if trash_to_apply[0].root is not None
                else self.target
            )
            append_trash(done_trash, root=trash_root)
            trashed = len(done_trash)

        if self.do_clean and not self.do_organize:
            parts = [f"A papelera: {trashed}."]
        else:
            parts = [f"Movidos: {moved}.", f"A papelera: {trashed}."]
            if tagged:
                parts.append(f"Etiquetados: {tagged}.")
            parts.append("Puedes deshacer la organización desde el historial.")
        batches = list_history_batches()
        return {
            "ok": True,
            "message": " ".join(parts),
            "moved": moved,
            "trashed": trashed,
            "tagged": tagged,
            "can_undo": any(batch.get("can_undo") for batch in batches),
            "has_history": bool(batches),
        }

    def history_batches(self) -> dict[str, Any]:
        batches = list_history_batches()
        return {
            "batches": batches,
            "has_history": bool(batches),
            "can_undo": any(batch.get("can_undo") for batch in batches),
        }

    def undo_status(self) -> dict[str, Any]:
        batches = list_history_batches()
        payload = _undo_payload(summarize_batch(last_reversible_batch()))
        payload["has_history"] = bool(batches)
        payload["batches"] = batches
        return payload

    def undo_preview(self, timestamp: str | None = None) -> dict[str, Any]:
        if timestamp:
            batch = reversible_batch_at(str(timestamp))
        else:
            batch = last_reversible_batch()
            timestamp = batch[0].get("timestamp") if batch else None
        payload = _undo_payload(summarize_batch(batch))
        payload["timestamp"] = timestamp
        return payload

    def apply_undo(self, timestamp: str | None = None) -> dict[str, Any]:
        if timestamp:
            batch = reversible_batch_at(str(timestamp))
            batch_ts = str(timestamp)
        else:
            batch = last_reversible_batch()
            batch_ts = str(batch[0].get("timestamp")) if batch else ""
        summary = summarize_batch(batch)
        if not summary.available:
            return {"ok": False, "error": "No hay una organización para deshacer."}
        outcome = execute_undo(summary)
        if not outcome.did_something:
            return {
                "ok": False,
                "error": "Nada que deshacer. Los archivos ya no están en el destino.",
            }
        append_undos(outcome.restored, batch_timestamp=batch_ts or None)
        batches = list_history_batches()
        return {
            "ok": True,
            "message": _undo_message(outcome),
            "can_undo": any(batch.get("can_undo") for batch in batches),
            "has_history": bool(batches),
        }

    def reset_operation(self) -> dict[str, Any]:
        self.move_actions = []
        self.trash_candidates = []
        self.selected_trash_paths = None
        self.tag_mapping = {}
        self.use_ai = False
        self.do_search = False
        self.request = OrganizeRequest()
        return {"ok": True}

    def close_app(self) -> None:
        for window in list(webview.windows):
            window.destroy()
