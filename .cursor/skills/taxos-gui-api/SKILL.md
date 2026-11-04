---
name: taxos-gui-api
description: Guía el puente PyWebView entre la UI Vite y TaxosApi. Usar al cambiar GUI, app.js, TaxosApi, pywebview o el bridge UI↔Python.
---

# Bridge GUI — Taxos

## Regla de oro

La UI (`ui/src/app.js`) solo llama a `window.pywebview.api`. Toda lógica de negocio vive en Python (`TaxosApi` + núcleo).

## Contrato `TaxosApi` (`src/taxos/gui/api.py`)

| Método | Rol |
|--------|-----|
| `get_state` | Carpeta, tema, flags onboarding, clave Groq |
| `set_theme` / `set_folder` / `browse_folder` | Preferencias y ruta |
| `set_onboarding_flag` | Persistir `tutorial_seen` / `preview_tip_seen` / `undo_tip_seen` |
| `set_operation` / `set_organize_options` / `set_use_ai` | Opciones del asistente |
| `build_preview` | Plan de moves/trash/tags (sin mutar) |
| `apply_plan` | Aplicar + historial |
| `undo_status` / `undo_preview` / `apply_undo` | Deshacer |
| `reset_operation` / `close_app` | Ciclo de vida |

Payloads: dicts JSON-serializables (paths como `str`).

## Dev

```bash
cd ui && npm run dev
# otra terminal:
TAXOS_UI_DEV=1 taxos gui
```

Build UI: `cd ui && npm run build`.

## Al cambiar la API

1. Actualizar método en `TaxosApi`.
2. Actualizar llamada en `ui/src/app.js`.
3. Verificar preview y apply en el asistente.
4. No duplicar `plan_moves` / clasificación en JS.
