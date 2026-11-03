"""Rutas multiplataforma para Taxos."""

from pathlib import Path

from platformdirs import user_downloads_dir


def get_downloads_dir() -> Path:
    """Devuelve la carpeta Descargas del usuario (sin crearla)."""
    home = Path.home()
    for name in ("Downloads", "Descargas"):
        candidate = home / name
        if candidate.is_dir():
            return candidate

    platform_path = Path(user_downloads_dir())
    if platform_path.is_dir():
        return platform_path

    return home / "Downloads"
