# Taxos

Organiza la carpeta Descargas en Windows y Linux: clasifica, mueve y limpia con preview antes de aplicar. Habrá CLI para desarrollo y un wizard gráfico para quien no use terminal. La IA (opcional) solo ve nombres de archivo, nunca el contenido.

## Stack

- Python 3.11+, Typer, Rich, pathlib, platformdirs, send2trash, YAML
- GUI: CustomTkinter (fase 4) · IA nombres: Groq u similar (fase 5)

## Privacidad

Sin IA no sale nada del PC. Con IA opt-in solo se envían nombres de archivo.

## Instalación (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
taxos path
taxos scan
taxos organize              # dry-run
taxos organize --apply      # mueve tras confirmar
```

## Guía

Fases en [docs/ROADMAP.md](docs/ROADMAP.md). Repo pensado para ser público y auditable.
