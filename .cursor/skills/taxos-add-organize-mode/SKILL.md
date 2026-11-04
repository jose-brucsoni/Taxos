---
name: taxos-add-organize-mode
description: Añade o activa un modo de organización en Taxos (organize_modes, ORG_METHODS, API GUI, tests). Usar al crear un método nuevo o pasar uno de coming-soon a enabled.
---

# Nuevo modo de organización

## Decisión

- **Enabled ahora** → `ENABLED_METHODS` en `src/taxos/organize_modes.py`.
- **Coming soon** → `COMING_SOON_METHODS` + `enabled: false` en JS.
- `content` y `rules` siguen fuera de alcance (no activar sin pedirlo).

## Pasos

1. **Python** — `normalize_request` / `plan_moves` (o tags) en `organize_modes.py`.
2. **API** — exponer opciones en `TaxosApi.set_organize_options` / `build_preview` si hace falta.
3. **UI** — entrada en `ORG_METHODS` en `ui/src/app.js` (`id`, título, descripción, `enabled`, icono).
4. **Sync** — mismo `id` en JS y Python.
5. **Test** — caso en `tests/test_organize_modes.py` con `tmp_path` (nunca Descargas real).
6. **Verificar** — preview en GUI muestra origen→destino (o etiquetas) sin mutar hasta apply.

## Checklist

- [ ] Nombres de carpeta vía `sanitize_label`
- [ ] Sin leer contenido de archivos
- [ ] Dry-run / preview antes de apply
- [ ] Historial si el modo mueve o escribe tags
