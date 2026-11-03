# Taxos

Organiza la carpeta Descargas en Windows y Linux: clasifica, mueve y limpia con preview antes de aplicar. La IA (opcional) solo ve nombres de archivo, nunca el contenido.

Licencia: [MIT](LICENSE).

## Para usuarios (Windows)

No necesitas instalar Python.

1. Ve a **Releases** en este repositorio.
2. Descarga `Taxos.exe` (Win64).
3. Doble clic → se abre el asistente gráfico.

Si Windows SmartScreen avisa: *Más información* → *Ejecutar de todas formas*.  
No empaquetes `.env` en el `.exe`. Sin clave, la IA del wizard no se usa (reglas locales).

## Para desarrolladores

### Stack

- Python 3.11+, Typer, Rich, pathlib, platformdirs, send2trash, YAML, httpx, watchdog
- GUI: CustomTkinter · IA: Groq (opt-in)

### Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env        # opcional: GROQ_API_KEY
taxos path
taxos scan
taxos organize              # dry-run
taxos organize --apply
taxos clean
taxos undo
taxos watch
taxos gui
```

### Generar ejecutables

**Windows 64-bit** (en un PC Windows; abre el wizard al doble clic):

```powershell
.\scripts\build_windows.ps1
# → dist\Taxos.exe  → súbelo a GitHub Releases
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

Luego, en Windows: genera `Taxos.exe` y súbelo en **Releases**.

## Guía

Fases en [docs/ROADMAP.md](docs/ROADMAP.md).
