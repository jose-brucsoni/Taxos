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


def run_webview() -> None:
    """Abre el wizard en una ventana PyWebView."""
    api = TaxosApi()
    url = _ui_url()
    webview.create_window(
        "Taxos — organizar Descargas",
        url=url,
        js_api=api,
        width=720,
        height=560,
        min_size=(480, 360),
    )
    webview.start()
