"""Wizard CustomTkinter: ruta → opciones → preview → aplicar."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from dotenv import load_dotenv

from taxos.classifier import classify_with_optional_ai
from taxos.cleaner import TrashCandidate, apply_trash, find_candidates
from taxos.config import load_rules
from taxos.history import append_moves, append_trash
from taxos.organizer import MoveAction, apply_plan, build_plan
from taxos.paths import get_downloads_dir
from taxos.scanner import scan_dir

load_dotenv()


class TaxosWizard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Taxos — organizar Descargas")
        self.geometry("640x480")
        self.minsize(520, 400)

        self.target = get_downloads_dir()
        self.do_organize = ctk.BooleanVar(value=True)
        self.do_clean = ctk.BooleanVar(value=False)
        self.use_ai = ctk.BooleanVar(value=False)
        self.step = 0
        self.move_actions: list[MoveAction] = []
        self.trash_candidates: list[TrashCandidate] = []

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=16, pady=16)

        self.nav = ctk.CTkFrame(self)
        self.nav.pack(fill="x", padx=16, pady=(0, 16))
        self.back_btn = ctk.CTkButton(self.nav, text="Atrás", width=100, command=self._back)
        self.next_btn = ctk.CTkButton(self.nav, text="Siguiente", width=120, command=self._next)
        self.back_btn.pack(side="left")
        self.next_btn.pack(side="right")

        self._show_step()

    def _clear_container(self) -> None:
        for child in self.container.winfo_children():
            child.destroy()

    def _show_step(self) -> None:
        self._clear_container()
        self.back_btn.configure(state="normal" if self.step > 0 else "disabled")
        if self.step == 0:
            self._step_path()
            self.next_btn.configure(text="Siguiente")
        elif self.step == 1:
            self._step_options()
            self.next_btn.configure(text="Siguiente")
        elif self.step == 2:
            self._step_preview()
            self.next_btn.configure(text="Aplicar…")
        else:
            self._step_done()
            self.next_btn.configure(text="Cerrar")

    def _step_path(self) -> None:
        ctk.CTkLabel(
            self.container,
            text="Carpeta a organizar",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(8, 4))
        ctk.CTkLabel(
            self.container,
            text="Por defecto se usa tu carpeta Descargas.",
            wraplength=560,
        ).pack(anchor="w", pady=(0, 12))

        self.path_label = ctk.CTkLabel(
            self.container,
            text=str(self.target),
            wraplength=560,
            justify="left",
        )
        self.path_label.pack(anchor="w", pady=(0, 12))
        ctk.CTkButton(self.container, text="Elegir otra carpeta…", command=self._browse).pack(
            anchor="w"
        )

    def _browse(self) -> None:
        chosen = filedialog.askdirectory(initialdir=str(self.target))
        if chosen:
            self.target = Path(chosen)
            self.path_label.configure(text=str(self.target))

    def _step_options(self) -> None:
        ctk.CTkLabel(
            self.container,
            text="¿Qué quieres hacer?",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(8, 12))

        ctk.CTkCheckBox(
            self.container,
            text="Organizar por categoría (mueve archivos de la raíz a subcarpetas)",
            variable=self.do_organize,
        ).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(
            self.container,
            text="Limpiar basura segura (tmp, vacíos, locks → papelera)",
            variable=self.do_clean,
        ).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(
            self.container,
            text="Usar IA (solo nombres de archivo; requiere GROQ_API_KEY)",
            variable=self.use_ai,
        ).pack(anchor="w", pady=6)
        ctk.CTkLabel(
            self.container,
            text="En el siguiente paso verás un preview antes de aplicar.",
            wraplength=560,
        ).pack(anchor="w", pady=(16, 0))

    def _build_plans(self) -> None:
        self.move_actions = []
        self.trash_candidates = []
        if not self.target.is_dir():
            return
        if self.do_organize.get():
            rules = load_rules()
            entries = scan_dir(self.target)
            classified, _note = classify_with_optional_ai(
                entries, rules, use_ai=self.use_ai.get()
            )
            self.move_actions = build_plan(self.target, classified)
        if self.do_clean.get():
            self.trash_candidates = find_candidates(self.target)

    def _step_preview(self) -> None:
        self._build_plans()
        ctk.CTkLabel(
            self.container,
            text="Preview del plan",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(8, 4))

        lines: list[str] = []
        if self.do_organize.get():
            lines.append(f"Movimientos: {len(self.move_actions)}")
            for action in self.move_actions[:50]:
                try:
                    rel = action.dest.relative_to(self.target)
                except ValueError:
                    rel = action.dest
                lines.append(f"  {action.src.name} → {rel}")
            if len(self.move_actions) > 50:
                lines.append(f"  … y {len(self.move_actions) - 50} más")
        if self.do_clean.get():
            if lines:
                lines.append("")
            lines.append(f"A papelera: {len(self.trash_candidates)}")
            for candidate in self.trash_candidates[:50]:
                lines.append(f"  {candidate.path.name} ({candidate.reason})")
            if len(self.trash_candidates) > 50:
                lines.append(f"  … y {len(self.trash_candidates) - 50} más")

        if not self.do_organize.get() and not self.do_clean.get():
            lines.append("No hay opciones activas. Vuelve atrás y elige al menos una.")
        elif not self.move_actions and not self.trash_candidates:
            lines.append("Nada que hacer en esta carpeta con las opciones elegidas.")

        box = ctk.CTkTextbox(self.container, wrap="word")
        box.pack(fill="both", expand=True, pady=(8, 0))
        box.insert("1.0", "\n".join(lines))
        box.configure(state="disabled")

    def _step_done(self) -> None:
        ctk.CTkLabel(
            self.container,
            text="Listo",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(8, 4))
        ctk.CTkLabel(
            self.container,
            text=getattr(self, "_result_message", "Operación terminada."),
            wraplength=560,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

    def _apply(self) -> bool:
        if not self.do_organize.get() and not self.do_clean.get():
            messagebox.showinfo("Taxos", "Activa al menos una opción.")
            return False
        if not self.move_actions and not self.trash_candidates:
            messagebox.showinfo("Taxos", "No hay acciones en el plan.")
            return False

        summary = (
            f"Se van a mover {len(self.move_actions)} archivo(s) "
            f"y enviar {len(self.trash_candidates)} a la papelera.\n\n¿Continuar?"
        )
        if not messagebox.askyesno("Confirmar", summary):
            return False

        moved = 0
        trashed = 0
        if self.move_actions:
            done = apply_plan(self.move_actions)
            append_moves(done)
            moved = len(done)
        if self.trash_candidates:
            done_trash = apply_trash(self.trash_candidates)
            append_trash(done_trash)
            trashed = len(done_trash)

        self._result_message = (
            f"Movidos: {moved}. A papelera: {trashed}.\n"
            "Puedes deshacer movimientos con: taxos undo"
        )
        return True

    def _back(self) -> None:
        if self.step > 0:
            self.step -= 1
            self._show_step()

    def _next(self) -> None:
        if self.step == 0:
            if not self.target.is_dir():
                messagebox.showerror("Taxos", f"No existe la carpeta:\n{self.target}")
                return
            self.step = 1
        elif self.step == 1:
            if not self.do_organize.get() and not self.do_clean.get():
                messagebox.showinfo("Taxos", "Elige al menos una opción.")
                return
            self.step = 2
        elif self.step == 2:
            if self._apply():
                self.step = 3
            else:
                return
        else:
            self.destroy()
            return
        self._show_step()


def run_wizard() -> None:
    """Arranca el wizard. Mensaje claro si no hay display o falta Tk."""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    try:
        app = TaxosWizard()
        app.mainloop()
    except Exception as exc:  # noqa: BLE001 — feedback al usuario sin display
        msg = str(exc).lower()
        if any(
            token in msg
            for token in ("display", "no display", "libtk", "tkinter", "_tkinter")
        ):
            raise RuntimeError(
                "No se pudo abrir la GUI (DISPLAY o libtk). Usa la CLI: taxos scan / organize."
            ) from exc
        raise
