"""API expuesta a JavaScript vía PyWebView."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import webview

from taxos.classifier import classify_with_optional_ai
from taxos.cleaner import TrashCandidate, apply_trash, find_candidates
from taxos.config import load_rules
from taxos.gui.prefs import load_gui_prefs, save_gui_prefs
from taxos.history import append_moves, append_trash
from taxos.organizer import MoveAction, apply_plan, build_plan
from taxos.paths import get_downloads_dir
from taxos.scanner import scan_dir


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


class TaxosApi:
    def __init__(self) -> None:
        self.target = get_downloads_dir()
        self.do_organize = True
        self.do_clean = False
        self.use_ai = False
        self.move_actions: list[MoveAction] = []
        self.trash_candidates: list[TrashCandidate] = []

    def get_state(self) -> dict[str, Any]:
        prefs = load_gui_prefs()
        return {
            "folder": str(self.target),
            "theme": prefs.get("appearance_mode", "Light"),
            "has_groq_key": _has_groq_key(),
            "do_organize": self.do_organize,
            "do_clean": self.do_clean,
            "use_ai": self.use_ai,
        }

    def set_theme(self, mode: str) -> dict[str, Any]:
        if mode not in {"System", "Light", "Dark"}:
            mode = "System"
        save_gui_prefs({"appearance_mode": mode})
        return {"ok": True, "theme": mode}

    def set_operation(self, kind: str) -> dict[str, Any]:
        if kind == "organize":
            self.do_organize, self.do_clean = True, False
        elif kind == "clean":
            self.do_organize, self.do_clean = False, True
        elif kind == "both":
            self.do_organize, self.do_clean = True, True
        else:
            return {"ok": False, "error": "Operación desconocida."}
        return {
            "ok": True,
            "do_organize": self.do_organize,
            "do_clean": self.do_clean,
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
            classified, _note = classify_with_optional_ai(
                entries, rules, use_ai=self.use_ai
            )
            self.move_actions = build_plan(self.target, classified)

        if self.do_clean:
            self.trash_candidates = find_candidates(self.target)

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

        if self.trash_candidates:
            trash_count = len(self.trash_candidates)
            trash_size = sum(c.size for c in self.trash_candidates)
            trash_files = [
                {
                    "name": c.path.name,
                    "size_bytes": c.size,
                    "size_label": _format_size(c.size),
                }
                for c in self.trash_candidates
            ]
            groups.append(
                {
                    "name": "Papelera",
                    "kind": "trash",
                    "count": trash_count,
                    "size_bytes": trash_size,
                    "size_label": _format_size(trash_size),
                    "files": trash_files,
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
        if self.do_clean:
            if lines:
                lines.append("")
            for candidate in self.trash_candidates[:50]:
                lines.append(f"{candidate.path.name} ({candidate.reason})")
            if len(self.trash_candidates) > 50:
                lines.append(f"… y {len(self.trash_candidates) - 50} más")

        if not self.move_actions and not self.trash_candidates:
            lines.append("Nada que hacer en esta carpeta con la operación elegida.")

        return {
            "move_count": len(self.move_actions),
            "trash_count": len(self.trash_candidates),
            "groups": groups,
            "lines": lines,
        }

    def apply_plan(self) -> dict[str, Any]:
        if not self.do_organize and not self.do_clean:
            return {"ok": False, "error": "No hay operación seleccionada."}
        if not self.move_actions and not self.trash_candidates:
            return {"ok": False, "error": "No hay acciones en el plan."}

        moved = 0
        trashed = 0
        if self.move_actions:
            done = apply_plan(self.move_actions)
            append_moves(done)
            moved = len(done)
        if self.trash_candidates:
            done_trash = apply_trash(self.trash_candidates)
            append_trash(done_trash)
            trashed = len(done_trash)

        message = (
            f"Movidos: {moved}. A papelera: {trashed}.\n"
            "Puedes deshacer movimientos con: taxos undo"
        )
        return {"ok": True, "message": message, "moved": moved, "trashed": trashed}

    def reset_operation(self) -> dict[str, Any]:
        self.move_actions = []
        self.trash_candidates = []
        self.use_ai = False
        return {"ok": True}

    def close_app(self) -> None:
        for window in list(webview.windows):
            window.destroy()
