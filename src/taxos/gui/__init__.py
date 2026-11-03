"""Interfaz gráfica de Taxos."""

from __future__ import annotations


def run_wizard() -> None:
    """Carga el wizard bajo demanda (requiere Tk/CustomTkinter)."""
    from taxos.gui.wizard import run_wizard as _run_wizard

    _run_wizard()


__all__ = ["run_wizard"]
