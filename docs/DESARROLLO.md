# Desarrollo — Taxos

Guía técnica para quien programa o empaqueta Taxos. La guía de uso está en el [README](../README.md).

## Stack

- Python 3.11+, Typer, Rich, pathlib, platformdirs, send2trash, YAML, httpx, watchdog
- GUI: PyWebView + Vite/Tailwind · IA: Groq (opt-in)
- Windows GUI: WebView2 Runtime (suele venir con Microsoft Edge)

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env        # opcional: GROQ_API_KEY

# UI (Node 20+):
cd ui && npm install && npm run build && cd ..

taxos path
taxos scan
taxos organize              # dry-run
taxos organize --apply
taxos clean
taxos undo
taxos watch
taxos gui
```

Desarrollo de la UI con hot-reload:

```bash
cd ui && npm run dev
# otra terminal:
set TAXOS_UI_DEV=1          # PowerShell: $env:TAXOS_UI_DEV=1
taxos gui
```

## Generar ejecutables

**Windows 64-bit** (en un PC Windows; carpeta onedir; el script construye la UI con npm):

```powershell
.\scripts\build_windows.ps1
# → dist\Taxos\Taxos.exe
# → dist\Taxos-win64.zip  → súbelo a GitHub Releases
```

**Linux** (CLI one-file + AppImage GUI):

```bash
./scripts/build_linux.sh
# → dist/taxos
# → dist/Taxos-x86_64.AppImage  (requiere appimagetool en PATH)
```

Instala [appimagetool](https://github.com/AppImage/appimagetool/releases) para generar el `.AppImage`. Sin él, el script deja listo `dist/Taxos.AppDir`.

No empaquetes `.env` en el binario.

## Publicar en GitHub

1. Crea un repositorio vacío y **público** (sin README).
2. En este proyecto:

```bash
git remote add origin https://github.com/TU_USUARIO/Taxos.git
git branch -M main
git push -u origin main
```

Luego, en Windows: `.\scripts\build_windows.ps1` y sube `dist\Taxos-win64.zip` en **Releases**.

## Guía de fases

Fases del proyecto en [ROADMAP.md](ROADMAP.md).
