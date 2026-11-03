"""Interfaz gráfica de Taxos (PyWebView)."""

from __future__ import annotations


def run_wizard() -> None:
    """Abre el wizard web embebido."""
    from taxos.gui.webview_app import run_webview

    run_webview()


__all__ = ["run_wizard"]
