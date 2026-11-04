#!/usr/bin/env bash
# Genera dist/taxos (CLI one-file) y, si hay appimagetool, dist/Taxos-*.AppImage (GUI).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

if command -v npm >/dev/null 2>&1; then
  (
    cd ui
    if [[ ! -d node_modules ]]; then
      npm ci || npm install
    fi
    npm run build
  )
else
  echo "Aviso: npm no está en PATH; se usa ui/dist existente si hay."
fi

"$PYTHON" -m pip install -e ".[build]"

# CLI one-file
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name taxos \
  --paths src \
  --collect-data taxos \
  --hidden-import taxos.gui.webview_app \
  --hidden-import taxos.gui.api \
  src/taxos/cli.py

echo "Binario CLI: $ROOT/dist/taxos"

# GUI onedir → AppImage
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --onedir \
  --name Taxos \
  --paths src \
  --collect-data taxos \
  --add-data "ui/dist:ui/dist" \
  --hidden-import taxos.gui.webview_app \
  --hidden-import taxos.gui.api \
  src/taxos/run_gui.py

APPDIR="$ROOT/dist/Taxos.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp -a "$ROOT/dist/Taxos/." "$APPDIR/usr/bin/"

# Icono PNG mínimo (256x256) generado con Pillow si está; si no, copia SVG como fallback no-AppStream.
ICON_PNG="$APPDIR/usr/share/icons/hicolor/256x256/apps/taxos.png"
"$PYTHON" - <<'PY' "$ICON_PNG"
import sys
from pathlib import Path

out = Path(sys.argv[1])
try:
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (256, 256), (28, 25, 23, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((40, 40, 216, 216), radius=28, fill=(250, 250, 249, 255))
    draw.rectangle((72, 88, 184, 104), fill=(28, 25, 23, 255))
    draw.rectangle((72, 120, 160, 136), fill=(68, 64, 60, 255))
    draw.rectangle((72, 152, 144, 168), fill=(120, 113, 108, 255))
    img.save(out)
except Exception:
    out.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f"
        b"\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
PY
cp -f "$ICON_PNG" "$APPDIR/taxos.png"

cat > "$APPDIR/taxos.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Taxos
Comment=Organiza y limpia carpetas de descargas
Exec=Taxos
Icon=taxos
Categories=Utility;FileTools;
Terminal=false
EOF
cp -f "$APPDIR/taxos.desktop" "$APPDIR/usr/share/applications/taxos.desktop"

cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/Taxos" "$@"
EOF
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/bin/Taxos"

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) APPIMAGE_ARCH="x86_64" ;;
  aarch64|arm64) APPIMAGE_ARCH="aarch64" ;;
  *) APPIMAGE_ARCH="$ARCH" ;;
esac
OUT_APPIMAGE="$ROOT/dist/Taxos-${APPIMAGE_ARCH}.AppImage"

if command -v appimagetool >/dev/null 2>&1; then
  ARCH="$APPIMAGE_ARCH" appimagetool "$APPDIR" "$OUT_APPIMAGE"
  echo "AppImage: $OUT_APPIMAGE"
else
  echo "Aviso: appimagetool no está en PATH."
  echo "  Instálalo (https://github.com/AppImage/appimagetool/releases) y vuelve a ejecutar este script."
  echo "  AppDir listo en: $APPDIR"
fi
