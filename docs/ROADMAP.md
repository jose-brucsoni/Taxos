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

- [ ] Candidatos seguros (tmp, vacíos, etc.)
- [ ] Papelera (`send2trash`)
- [ ] Deshacer desde el log

## Fase 4 — GUI wizard

- [ ] CustomTkinter: preguntas (cómo organizar / qué conservar)
- [ ] Preview del plan
- [ ] Confirmar y aplicar (usa el núcleo)

## Fase 5 — IA opcional

- [ ] Opt-in; solo nombres de archivo (Groq u similar)
- [ ] Sugerir carpetas / agrupar por significado
- [ ] Sin IA = reglas locales offline

## Fase 6 — Distribución

- [ ] One-click: PyInstaller (Win) + binario/AppImage (Linux)
- [ ] `taxos watch` si aplica
- [ ] LICENSE (MIT) y repo público

## Principios

- Dry-run / preview antes de mutar
- Solo Descargas (o ruta que indique el usuario)
- Borrar a papelera, no irreversible
- IA desactivada por defecto; no subir contenido de archivos

## Fuera de alcance (por ahora)

- Analizar el contenido interno de los archivos con IA
