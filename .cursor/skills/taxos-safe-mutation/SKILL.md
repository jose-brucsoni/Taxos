---
name: taxos-safe-mutation
description: Aplica el flujo seguro de mutación de archivos en Taxos (preview, confirmación, apply, historial, undo, papelera). Usar al tocar organize, clean, undo, watch, dry-run o apply.
---

# Mutación segura — Taxos

## Flujo obligatorio

1. **Preview / dry-run**: construir plan sin escribir disco.
2. **Confirmación**: el usuario (CLI o GUI) confirma antes de apply.
3. **Apply**: mover o enviar a papelera.
4. **Historial**: registrar lote en `history` (append-only).
5. **Undo**: el último lote reversible debe poder deshacerse.

## Checklist

- [ ] No mutar fuera de la raíz (Descargas o ruta explícita).
- [ ] Borrar solo con `send2trash`, no `unlink`.
- [ ] Colisiones: destino único, no sobrescribir.
- [ ] Watch: esperar settle antes de organizar.
- [ ] Fallo de un archivo no tumba el lote entero si se puede continuar.

## Módulos

- Plan/apply: `src/taxos/organizer.py`, `src/taxos/organize_modes.py`
- Limpieza: `src/taxos/cleaner.py`
- Log: `src/taxos/history.py`
- Deshacer: `src/taxos/undo.py`
- Watch: `src/taxos/watcher.py`
