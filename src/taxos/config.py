"""Carga de reglas de clasificación."""

from importlib import resources
from pathlib import Path

import yaml


def load_rules(rules_path: Path | None = None) -> dict[str, list[str]]:
    """Carga categorías → extensiones desde YAML (paquete o ruta)."""
    if rules_path is not None:
        text = rules_path.read_text(encoding="utf-8")
    else:
        text = (
            resources.files("taxos")
            .joinpath("default_rules.yaml")
            .read_text(encoding="utf-8")
        )

    data = yaml.safe_load(text) or {}
    categories = data.get("categories") or {}
    return {
        name: [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in exts]
        for name, exts in categories.items()
    }


def extension_index(rules: dict[str, list[str]]) -> dict[str, str]:
    """Mapa extensión → categoría (última gana si hay solape)."""
    index: dict[str, str] = {}
    for category, extensions in rules.items():
        for ext in extensions:
            index[ext.lower()] = category
    return index
