# Roadmap Taxos

Núcleo CLI primero; luego wizard GUI; IA opcional; al final instalable.

## Fase 0 — Base

- [x] Entorno virtual e dependencias
- [x] Estructura `src/taxos/`
- [x] Detectar Descargas (Win/Linux)

## Fase 1 — Scan y classify

- [x] Listar archivos y metadatos
- [x] Clasificar por reglas YAML (extensión)
- [x] Comando `taxos scan`

## Fase 2 — Organize

- [x] Plan de movimientos
- [x] `taxos organize` (dry-run por defecto)
- [x] Aplicar con `--apply`, confirmación + log

## Fase 3 — Clean y undo

- [x] Candidatos seguros (tmp, vacíos, etc.)
- [x] Papelera (`send2trash`)
- [x] Deshacer desde el log

## Fase 4 — GUI wizard

- [x] PyWebView + Vite/Tailwind (asistente): preguntas (cómo organizar / qué conservar)
- [x] Preview del plan
- [x] Confirmar y aplicar (usa el núcleo)

## Fase 5 — IA opcional

- [x] Opt-in; solo nombres de archivo (Groq)
- [x] Sugerir carpetas / agrupar por significado
- [x] Sin IA = reglas locales offline

## Fase 6 — Distribución

- [x] One-click: PyInstaller (Win + binario Linux + AppImage vía `scripts/build_linux.sh`)
- [x] `taxos watch`
- [x] LICENSE (MIT); publicación GitHub documentada
- [x] `Taxos.exe` Win64 GUI (`run_gui` + `scripts/build_windows.ps1` → Releases)

## Principios

- Dry-run / preview antes de mutar
- Solo Descargas (o ruta que indique el usuario)
- Borrar a papelera, no irreversible
- IA desactivada por defecto; no subir contenido de archivos

## Fuera de alcance (por ahora)

- Analizar el contenido interno de los archivos con IA
