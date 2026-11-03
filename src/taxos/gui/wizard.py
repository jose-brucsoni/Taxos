"""Compatibilidad: el wizard Tk se reemplazó por PyWebView."""

from __future__ import annotations


def run_wizard() -> None:
    """Redirige al wizard web."""
    from taxos.gui.webview_app import run_webview

    run_webview()
