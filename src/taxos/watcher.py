"""Observa Descargas y organiza archivos nuevos al estabilizarse."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from taxos.classifier import classify_with_optional_ai
from taxos.config import load_rules
from taxos.history import append_moves
from taxos.organizer import apply_plan, build_plan
from taxos.scanner import FileEntry

SettleCallback = Callable[[str], None]


class _DownloadsHandler(FileSystemEventHandler):
    def __init__(
        self,
        root: Path,
        *,
        apply: bool,
        use_ai: bool,
        settle_seconds: float,
        on_message: SettleCallback | None = None,
    ) -> None:
        super().__init__()
        self.root = root.resolve()
        self.apply = apply
        self.use_ai = use_ai
        self.settle_seconds = settle_seconds
        self.on_message = on_message or (lambda _msg: None)
        self._timers: dict[Path, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_created(self, event: FileSystemEvent) -> None:
        self._schedule(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._schedule(event)

    def _schedule(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.parent.resolve() != self.root:
            return
        if path.name.startswith("."):
            return

        with self._lock:
            existing = self._timers.pop(path, None)
            if existing is not None:
                existing.cancel()
            timer = threading.Timer(
                self.settle_seconds, self._process, args=(path,)
            )
            self._timers[path] = timer
            timer.daemon = True
            timer.start()

    def _process(self, path: Path) -> None:
        with self._lock:
            self._timers.pop(path, None)

        if not path.is_file():
            return
        if not self._is_stable(path):
            self._schedule_path(path)
            return

        self._organize_file(path)

    def _schedule_path(self, path: Path) -> None:
        with self._lock:
            timer = threading.Timer(
                self.settle_seconds, self._process, args=(path,)
            )
            self._timers[path] = timer
            timer.daemon = True
            timer.start()

    def _is_stable(self, path: Path) -> bool:
        try:
            size1 = path.stat().st_size
            time.sleep(0.4)
            size2 = path.stat().st_size
        except OSError:
            return False
        return size1 == size2

    def _organize_file(self, path: Path) -> None:
        try:
            stat = path.stat()
        except OSError:
            return

        from datetime import datetime

        entry = FileEntry(
            path=path,
            size=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime),
        )
        rules = load_rules()
        classified, _note = classify_with_optional_ai(
            [entry], rules, use_ai=self.use_ai
        )
        actions = build_plan(self.root, classified)
        if not actions:
            return

        action = actions[0]
        mode = "APPLY" if self.apply else "DRY-RUN"
        self.on_message(
            f"[{mode}] {action.src.name} → {action.dest.relative_to(self.root)}"
        )
        if not self.apply:
            return

        done = apply_plan(actions)
        if done:
            append_moves(done)


def run_watch(
    root: Path,
    *,
    apply: bool = False,
    use_ai: bool = False,
    settle_seconds: float = 1.5,
    on_message: SettleCallback | None = None,
) -> Observer:
    """Inicia el observer (bloqueante vía caller.join)."""
    root = root.resolve()
    handler = _DownloadsHandler(
        root,
        apply=apply,
        use_ai=use_ai,
        settle_seconds=settle_seconds,
        on_message=on_message,
    )
    observer = Observer()
    observer.schedule(handler, str(root), recursive=False)
    observer.start()
    return observer
