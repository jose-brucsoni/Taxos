"""Wizard CustomTkinter: ruta → opciones → preview → aplicar."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from dotenv import load_dotenv

from taxos.classifier import classify_with_optional_ai
from taxos.cleaner import TrashCandidate, apply_trash, find_candidates
from taxos.config import load_rules
from taxos.gui.prefs import load_gui_prefs, save_gui_prefs
from taxos.history import append_moves, append_trash
from taxos.organizer import MoveAction, apply_plan, build_plan
from taxos.paths import get_downloads_dir
from taxos.scanner import scan_dir

load_dotenv()

_STEP_TITLES = ("Carpeta", "Opciones", "Preview", "Listo")
_MODE_LABELS = {"System": "Sistema", "Light": "Claro", "Dark": "Oscuro"}
_LABEL_TO_MODE = {v: k for k, v in _MODE_LABELS.items()}


class TaxosWizard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Taxos — organizar Descargas")
        self.minsize(480, 360)

        self.target = get_downloads_dir()
        self.do_organize = ctk.BooleanVar(value=True)
        self.do_clean = ctk.BooleanVar(value=False)
        self.use_ai = ctk.BooleanVar(value=False)
        self.step = 0
        self.move_actions: list[MoveAction] = []
        self.trash_candidates: list[TrashCandidate] = []
        self._wrap_labels: list[ctk.CTkLabel] = []
        self._result_message = "Operación terminada."

        prefs = load_gui_prefs()
        self._appearance_mode = prefs["appearance_mode"]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer()
        self._center_window(720, 520)
        self.bind("<Configure>", self._on_resize)
        self._show_step()

    def _center_window(self, width: int, height: int) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Taxos",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.step_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray70"),
        )
        self.step_label.grid(row=0, column=1, sticky="w", padx=(16, 0))

        self.theme_btn = ctk.CTkSegmentedButton(
            header,
            values=["Sistema", "Claro", "Oscuro"],
            command=self._on_theme_change,
            width=220,
        )
        self.theme_btn.set(_MODE_LABELS.get(self._appearance_mode, "Sistema"))
        self.theme_btn.grid(row=0, column=2, sticky="e")

    def _build_body(self) -> None:
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=20, pady=4)
        self.body.grid_columnconfigure(0, weight=1)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 16))
        footer.grid_columnconfigure(1, weight=1)

        self.back_btn = ctk.CTkButton(
            footer,
            text="Atrás",
            width=100,
            command=self._back,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray90"),
        )
        self.next_btn = ctk.CTkButton(
            footer, text="Siguiente", width=130, command=self._next,
        )
        self.back_btn.grid(row=0, column=0, sticky="w")
        self.next_btn.grid(row=0, column=2, sticky="e")

    def _on_theme_change(self, value: str) -> None:
        mode = _LABEL_TO_MODE.get(value, "System")
        self._appearance_mode = mode
        ctk.set_appearance_mode(mode)
        save_gui_prefs({"appearance_mode": mode})

    def _wrap_width(self) -> int:
        return max(280, self.winfo_width() - 80)

    def _track_wrap(self, label: ctk.CTkLabel) -> ctk.CTkLabel:
        self._wrap_labels.append(label)
        label.configure(wraplength=self._wrap_width())
        return label

    def _on_resize(self, _event=None) -> None:
        width = self._wrap_width()
        for label in self._wrap_labels:
            try:
                if label.winfo_exists():
                    label.configure(wraplength=width)
            except Exception:  # noqa: BLE001 — widget destruido durante resize
                pass

    def _clear_body(self) -> None:
        self._wrap_labels.clear()
        for child in self.body.winfo_children():
            child.destroy()

    def _show_step(self) -> None:
        self._clear_body()
        total = len(_STEP_TITLES)
        title = _STEP_TITLES[self.step]
        self.step_label.configure(text=f"Paso {self.step + 1} de {total} · {title}")
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

    def _section_title(self, text: str) -> None:
        ctk.CTkLabel(
            self.body,
            text=text,
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 6))

    def _section_subtitle(self, text: str) -> None:
        label = ctk.CTkLabel(
            self.body,
            text=text,
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray65"),
            justify="left",
            anchor="w",
        )
        self._track_wrap(label).pack(fill="x", pady=(0, 16))

    def _step_path(self) -> None:
        self._section_title("Carpeta a organizar")
        self._section_subtitle("Por defecto se usa tu carpeta Descargas.")

        row = ctk.CTkFrame(self.body, fg_color=("gray92", "gray20"), corner_radius=8)
        row.pack(fill="x", pady=(0, 12))
        row.grid_columnconfigure(0, weight=1)

        self.path_label = ctk.CTkLabel(
            row,
            text=str(self.target),
            justify="left",
            anchor="w",
        )
        self._track_wrap(self.path_label).grid(
            row=0, column=0, sticky="ew", padx=12, pady=12
        )
        ctk.CTkButton(
            row, text="Examinar…", width=110, command=self._browse,
        ).grid(row=0, column=1, padx=12, pady=12)

    def _browse(self) -> None:
        chosen = filedialog.askdirectory(initialdir=str(self.target))
        if chosen:
            self.target = Path(chosen)
            self.path_label.configure(text=str(self.target))

    def _option_row(
        self, title: str, hint: str, variable: ctk.BooleanVar
    ) -> None:
        frame = ctk.CTkFrame(self.body, fg_color=("gray92", "gray20"), corner_radius=8)
        frame.pack(fill="x", pady=6)
        ctk.CTkCheckBox(frame, text=title, variable=variable).pack(
            anchor="w", padx=14, pady=(12, 2)
        )
        hint_label = ctk.CTkLabel(
            frame,
            text=hint,
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray60"),
            justify="left",
            anchor="w",
        )
        self._track_wrap(hint_label).pack(fill="x", padx=14, pady=(0, 12))

    def _step_options(self) -> None:
        self._section_title("¿Qué quieres hacer?")
        self._section_subtitle("En el siguiente paso verás un preview antes de aplicar.")

        self._option_row(
            "Organizar por categoría",
            "Mueve archivos de la raíz a subcarpetas según su tipo.",
            self.do_organize,
        )
        self._option_row(
            "Limpiar basura segura",
            "Envía tmp, vacíos y locks a la papelera.",
            self.do_clean,
        )
        self._option_row(
            "Usar IA",
            "Solo nombres de archivo; requiere GROQ_API_KEY.",
            self.use_ai,
        )

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
        self._section_title("Preview del plan")

        counts = ctk.CTkFrame(self.body, fg_color="transparent")
        counts.pack(fill="x", pady=(0, 8))
        if self.do_organize.get():
            ctk.CTkLabel(
                counts,
                text=f"Movimientos: {len(self.move_actions)}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left", padx=(0, 16))
        if self.do_clean.get():
            ctk.CTkLabel(
                counts,
                text=f"A papelera: {len(self.trash_candidates)}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")

        lines: list[str] = []
        if self.do_organize.get():
            for action in self.move_actions[:50]:
                try:
                    rel = action.dest.relative_to(self.target)
                except ValueError:
                    rel = action.dest
                lines.append(f"{action.src.name} → {rel}")
            if len(self.move_actions) > 50:
                lines.append(f"… y {len(self.move_actions) - 50} más")
        if self.do_clean.get():
            if lines:
                lines.append("")
            for candidate in self.trash_candidates[:50]:
                lines.append(f"{candidate.path.name} ({candidate.reason})")
            if len(self.trash_candidates) > 50:
                lines.append(f"… y {len(self.trash_candidates) - 50} más")

        if not self.do_organize.get() and not self.do_clean.get():
            lines.append("No hay opciones activas. Vuelve atrás y elige al menos una.")
        elif not self.move_actions and not self.trash_candidates:
            lines.append("Nada que hacer en esta carpeta con las opciones elegidas.")

        box = ctk.CTkTextbox(self.body, wrap="word", height=260)
        box.pack(fill="both", expand=True, pady=(4, 0))
        box.insert("1.0", "\n".join(lines))
        box.configure(state="disabled")

    def _step_done(self) -> None:
        self._section_title("Listo")
        self._section_subtitle(self._result_message)

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
    prefs = load_gui_prefs()
    ctk.set_appearance_mode(prefs["appearance_mode"])
    ctk.set_default_color_theme("blue")
    try:
        app = TaxosWizard()
        app.update()
        app.deiconify()
        app.lift()
        app.focus_force()
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
