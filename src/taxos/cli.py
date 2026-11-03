"""CLI de Taxos."""

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from taxos.classifier import classify_with_optional_ai
from taxos.cleaner import apply_trash, find_candidates
from taxos.config import load_rules
from taxos.history import append_moves, append_trash, append_undos, last_move_batch
from taxos.organizer import apply_plan, build_plan
from taxos.paths import get_downloads_dir
from taxos.scanner import scan_dir
from taxos.undo import apply_undo, build_undo_plan

load_dotenv()

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
    use_ai: bool = typer.Option(
        False,
        "--ai",
        help="Clasificar con IA (solo nombres; requiere GROQ_API_KEY).",
    ),
) -> None:
    """Resume archivos de la raíz por categoría."""
    target = path or get_downloads_dir()
    if not target.is_dir():
        console.print(f"[red]No existe la carpeta:[/red] {target}")
        raise typer.Exit(code=1)

    rules = load_rules()
    entries = scan_dir(target)
    classified, ai_note = classify_with_optional_ai(entries, rules, use_ai=use_ai)
    if ai_note:
        console.print(f"[dim]{ai_note}[/dim]")

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


@app.command("organize")
def organize(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Carpeta a organizar (por defecto: Descargas).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Aplicar movimientos (por defecto solo dry-run).",
    ),
    use_ai: bool = typer.Option(
        False,
        "--ai",
        help="Clasificar con IA (solo nombres; requiere GROQ_API_KEY).",
    ),
) -> None:
    """Mueve archivos de la raíz a subcarpetas por categoría."""
    target = path or get_downloads_dir()
    if not target.is_dir():
        console.print(f"[red]No existe la carpeta:[/red] {target}")
        raise typer.Exit(code=1)

    rules = load_rules()
    entries = scan_dir(target)
    classified, ai_note = classify_with_optional_ai(entries, rules, use_ai=use_ai)
    if ai_note:
        console.print(f"[dim]{ai_note}[/dim]")
    actions = build_plan(target, classified)

    mode = "[green]APPLY[/green]" if apply else "[yellow]DRY-RUN[/yellow]"
    console.print(f"[bold]Carpeta:[/bold] {target}  ({mode})")
    console.print(f"[bold]Movimientos:[/bold] {len(actions)}")

    if not actions:
        console.print("[yellow]Nada que mover.[/yellow]")
        return

    table = Table(title="Plan de organización")
    table.add_column("Origen")
    table.add_column("Destino", style="cyan")
    for action in actions:
        table.add_row(action.src.name, str(action.dest.relative_to(target)))
    console.print(table)

    if not apply:
        console.print("[dim]Dry-run: no se movió nada. Usa --apply para ejecutar.[/dim]")
        return

    if not typer.confirm("¿Aplicar estos movimientos?"):
        console.print("[yellow]Cancelado.[/yellow]")
        raise typer.Exit(code=0)

    done = apply_plan(actions)
    log_path = append_moves(done)
    console.print(f"[green]Movidos:[/green] {len(done)} / {len(actions)}")
    console.print(f"[bold]Log:[/bold] {log_path}")


@app.command("clean")
def clean(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Carpeta a limpiar (por defecto: Descargas).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Enviar a papelera (por defecto solo dry-run).",
    ),
) -> None:
    """Envía a papelera temporales, vacíos y locks seguros."""
    target = path or get_downloads_dir()
    if not target.is_dir():
        console.print(f"[red]No existe la carpeta:[/red] {target}")
        raise typer.Exit(code=1)

    candidates = find_candidates(target)
    mode = "[green]APPLY[/green]" if apply else "[yellow]DRY-RUN[/yellow]"
    console.print(f"[bold]Carpeta:[/bold] {target}  ({mode})")
    console.print(f"[bold]Candidatos:[/bold] {len(candidates)}")

    if not candidates:
        console.print("[yellow]Nada que limpiar.[/yellow]")
        return

    table = Table(title="Plan de limpieza")
    table.add_column("Archivo")
    table.add_column("Motivo", style="cyan")
    table.add_column("Tamaño", justify="right")
    for candidate in candidates:
        table.add_row(candidate.path.name, candidate.reason, _format_size(candidate.size))
    console.print(table)

    if not apply:
        console.print("[dim]Dry-run: no se borró nada. Usa --apply para enviar a papelera.[/dim]")
        return

    if not typer.confirm("¿Enviar estos archivos a la papelera?"):
        console.print("[yellow]Cancelado.[/yellow]")
        raise typer.Exit(code=0)

    done = apply_trash(candidates)
    log_path = append_trash(done)
    console.print(f"[green]A papelera:[/green] {len(done)} / {len(candidates)}")
    console.print(f"[bold]Log:[/bold] {log_path}")


@app.command("undo")
def undo(
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Aplicar deshacer (por defecto solo dry-run).",
    ),
) -> None:
    """Deshace el último lote de organize (desde el log)."""
    batch = last_move_batch()
    mode = "[green]APPLY[/green]" if apply else "[yellow]DRY-RUN[/yellow]"
    console.print(f"[bold]Undo último lote[/bold]  ({mode})")

    if not batch:
        console.print("[yellow]No hay movimientos en el historial.[/yellow]")
        return

    actions = build_undo_plan(batch)
    console.print(f"[bold]Restauraciones:[/bold] {len(actions)}")

    if not actions:
        console.print(
            "[yellow]Nada que deshacer (archivos ya no están en el destino).[/yellow]"
        )
        return

    table = Table(title="Plan de undo")
    table.add_column("Desde")
    table.add_column("Hacia", style="cyan")
    for action in actions:
        table.add_row(str(action.src), str(action.dest))
    console.print(table)

    if not apply:
        console.print("[dim]Dry-run: no se movió nada. Usa --apply para restaurar.[/dim]")
        return

    if not typer.confirm("¿Deshacer estos movimientos?"):
        console.print("[yellow]Cancelado.[/yellow]")
        raise typer.Exit(code=0)

    done = apply_undo(actions)
    log_path = append_undos(done)
    console.print(f"[green]Restaurados:[/green] {len(done)} / {len(actions)}")
    console.print(f"[bold]Log:[/bold] {log_path}")


@app.command("gui")
def gui() -> None:
    """Abre el wizard gráfico (PyWebView)."""
    try:
        from taxos.gui import run_wizard
    except ImportError as exc:
        console.print(
            "[red]Falta pywebview.[/red] Ejecuta: pip install -e ."
        )
        raise typer.Exit(code=1) from exc

    try:
        run_wizard()
    except ImportError as exc:
        console.print(
            "[red]No se pudo cargar la GUI web (pywebview).[/red] "
            "En Windows hace falta WebView2 Runtime (suele venir con Edge)."
        )
        console.print(f"[dim]{exc}[/dim]")
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.command("watch")
def watch(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Carpeta a observar (por defecto: Descargas).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Organizar automáticamente (por defecto solo dry-run).",
    ),
    use_ai: bool = typer.Option(
        False,
        "--ai",
        help="Usar IA al clasificar archivos nuevos.",
    ),
) -> None:
    """Observa la carpeta y organiza archivos nuevos al estabilizarse."""
    from taxos.watcher import run_watch

    target = path or get_downloads_dir()
    if not target.is_dir():
        console.print(f"[red]No existe la carpeta:[/red] {target}")
        raise typer.Exit(code=1)

    mode = "[green]APPLY[/green]" if apply else "[yellow]DRY-RUN[/yellow]"
    console.print(f"[bold]Observando:[/bold] {target}  ({mode})")
    console.print("[dim]Ctrl+C para salir.[/dim]")

    observer = run_watch(
        target,
        apply=apply,
        use_ai=use_ai,
        on_message=lambda msg: console.print(msg),
    )
    try:
        while observer.is_alive():
            observer.join(timeout=1.0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Watch detenido.[/yellow]")
    finally:
        observer.stop()
        observer.join(timeout=5.0)


if __name__ == "__main__":
    app()
