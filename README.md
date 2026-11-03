# Taxos

Organiza la carpeta Descargas en Windows y Linux: clasifica, mueve y limpia con preview antes de aplicar. La IA (opcional) solo ve nombres de archivo, nunca el contenido.

Licencia: [MIT](LICENSE). Ilustraciones e iconos de terceros: [docs/CREDITOS.md](docs/CREDITOS.md).

## Para usuarios (Windows)

No necesitas instalar Python.

1. **Ve a Releases en este repositorio.**
2. Descarga `Taxos-win64.zip`.
3. Descomprime la carpeta.
4. Doble clic en `Taxos.exe` para abrir el asistente.

Si Windows SmartScreen avisa: *Más información* → *Ejecutar de todas formas*.  
No hace falta (ni debes) meter un `.env` en esa carpeta para uso básico. Sin clave de IA se usan solo reglas locales.

## Para desarrolladores

### Stack

- Python 3.11+, Typer, Rich, pathlib, platformdirs, send2trash, YAML, httpx, watchdog
- GUI: PyWebView + Vite/Tailwind · IA: Groq (opt-in)
- Windows GUI: WebView2 Runtime (suele venir con Microsoft Edge)

### Instalación

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

### Generar ejecutables

**Windows 64-bit** (en un PC Windows; carpeta onedir; el script construye la UI con npm):

```powershell
.\scripts\build_windows.ps1
# → dist\Taxos\Taxos.exe
# → dist\Taxos-win64.zip  → súbelo a GitHub Releases
```

**Linux** (CLI one-file):

```bash
./scripts/build_linux.sh
# → dist/taxos
```

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

## Guía

Fases en [docs/ROADMAP.md](docs/ROADMAP.md).
