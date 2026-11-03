"""Arranque de la ventana PyWebView + UI embebida."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import webview

from taxos.gui.api import TaxosApi


def _ui_dist_dir() -> Path:
    """Ruta a ui/dist (dev, editable o bundle PyInstaller)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / "ui" / "dist"
        if bundled.is_dir():
            return bundled

    # src/taxos/gui/webview_app.py → repo root = parents[3]
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "ui" / "dist",
        Path.cwd() / "ui" / "dist",
    ]
    for path in candidates:
        if (path / "index.html").is_file():
            return path
    return candidates[0]


def _ui_url() -> str:
    if os.environ.get("TAXOS_UI_DEV", "").strip() in {"1", "true", "yes"}:
        return "http://127.0.0.1:5173"

    dist = _ui_dist_dir()
    index = dist / "index.html"
    if not index.is_file():
        raise RuntimeError(
            "No se encontró ui/dist/index.html. "
            "Ejecuta: cd ui && npm install && npm run build "
            "(o TAXOS_UI_DEV=1 con npm run dev)."
        )
    return index.resolve().as_uri()


def _screen_size() -> tuple[int, int]:
    """Tamaño de la pantalla primaria (ancho, alto)."""
    try:
        screens = getattr(webview, "screens", None)
        if screens:
            screen = screens[0]
            w = int(getattr(screen, "width", 0) or 0)
            h = int(getattr(screen, "height", 0) or 0)
            if w > 0 and h > 0:
                return w, h
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes

            user32 = ctypes.windll.user32
            return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
        except Exception:
            pass

    return 1280, 800


def run_webview() -> None:
    """Abre el wizard en una ventana PyWebView (~70% de la pantalla)."""
    api = TaxosApi()
    url = _ui_url()
    sw, sh = _screen_size()
    width = max(640, int(sw * 0.7))
    height = max(480, int(sh * 0.7))
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    webview.create_window(
        "Taxos",
        url=url,
        js_api=api,
        width=width,
        height=height,
        x=x,
        y=y,
        min_size=(640, 480),
    )
    webview.start()
