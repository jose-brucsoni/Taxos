# Taxos

Organiza la carpeta Descargas en Windows y Linux: clasifica, mueve y limpia con preview antes de aplicar. CLI + wizard gráfico. La IA (opcional) solo ve nombres de archivo, nunca el contenido.

Licencia: [MIT](LICENSE).

## Stack

- Python 3.11+, Typer, Rich, pathlib, platformdirs, send2trash, YAML, httpx, watchdog
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
taxos organize              # dry-run
taxos organize --apply
taxos clean
taxos undo
taxos watch                 # dry-run al detectar archivos nuevos
taxos gui
```

## Binario (one-click)

**Linux:**

```bash
pip install -e ".[build]"
./scripts/build_linux.sh
./dist/taxos --help
```

**Windows** (PowerShell, con venv activo):

```powershell
pip install -e ".[build]"
pyinstaller --noconfirm --clean --onefile --name taxos --paths src --collect-data taxos --hidden-import taxos.gui.wizard src/taxos/cli.py
.\dist\taxos.exe --help
```

(AppImage / instalador `.msi` quedan para más adelante.)

## Publicar en GitHub

1. Crea un repositorio vacío y **público** en GitHub (sin README).
2. En este proyecto:

```bash
git remote add origin https://github.com/TU_USUARIO/Taxos.git
git branch -M main
git push -u origin main
```

No subas `.env`.

## Guía

Fases en [docs/ROADMAP.md](docs/ROADMAP.md).
