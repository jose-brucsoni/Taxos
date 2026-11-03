# Taxos

Organiza la carpeta Descargas en Windows y Linux: clasifica, mueve y limpia con preview antes de aplicar. CLI + wizard gráfico. La IA (opcional) solo ve nombres de archivo, nunca el contenido.

## Stack

- Python 3.11+, Typer, Rich, pathlib, platformdirs, send2trash, YAML, httpx
- GUI: CustomTkinter · IA: Groq (opt-in)

## Privacidad

Sin IA no sale nada del PC. Con `--ai` / checkbox solo se envían nombres. Clave en `.env` (`GROQ_API_KEY`), nunca en git.

## Instalación (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env        # y añade tu GROQ_API_KEY
taxos path
taxos scan
taxos scan --ai
taxos organize              # dry-run
taxos organize --ai         # dry-run + IA
taxos organize --apply
taxos clean
taxos undo
taxos gui
```

## Guía

Fases en [docs/ROADMAP.md](docs/ROADMAP.md). Repo pensado para ser público y auditable.
