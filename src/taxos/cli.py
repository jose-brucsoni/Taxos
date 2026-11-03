"""CLI de Taxos."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from taxos.classifier import classify_all
from taxos.config import load_rules
from taxos.paths import get_downloads_dir
from taxos.scanner import scan_dir

app = typer.Typer(help="Organiza la carpeta Descargas.", no_args_is_help=True)
console = Console()


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


@app.callback()
def _root() -> None:
    """Organiza la carpeta Descargas."""


@app.command("path")
def show_path() -> None:
    """Muestra la carpeta Descargas detectada."""
    downloads = get_downloads_dir()
    exists = "existe" if downloads.is_dir() else "no existe aún"
    console.print(f"[bold]Descargas:[/bold] {downloads} ({exists})")


@app.command("scan")
def scan(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Carpeta a escanear (por defecto: Descargas).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
) -> None:
    """Resume archivos de la raíz por categoría."""
    target = path or get_downloads_dir()
    if not target.is_dir():
        console.print(f"[red]No existe la carpeta:[/red] {target}")
        raise typer.Exit(code=1)

    rules = load_rules()
    entries = scan_dir(target)
    classified = classify_all(entries, rules)

    totals: dict[str, list[int]] = {}
    for entry, category in classified:
        count_size = totals.setdefault(category, [0, 0])
        count_size[0] += 1
        count_size[1] += entry.size

    console.print(f"[bold]Carpeta:[/bold] {target}")
    console.print(f"[bold]Archivos:[/bold] {len(entries)}")

    table = Table(title="Resumen por categoría")
    table.add_column("Categoría", style="cyan")
    table.add_column("Cantidad", justify="right")
    table.add_column("Tamaño", justify="right")

    for category in sorted(totals.keys()):
        count, size = totals[category]
        table.add_row(category, str(count), _format_size(size))

    if not totals:
        console.print("[yellow]No hay archivos en la raíz de esta carpeta.[/yellow]")
    else:
        console.print(table)

    if 0 < len(classified) <= 20:
        detail = Table(title="Archivos")
        detail.add_column("Nombre")
        detail.add_column("Categoría", style="cyan")
        detail.add_column("Tamaño", justify="right")
        for entry, category in classified:
            detail.add_row(entry.name, category, _format_size(entry.size))
        console.print(detail)


if __name__ == "__main__":
    app()
