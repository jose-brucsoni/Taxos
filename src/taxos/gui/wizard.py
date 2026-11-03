"""Wizard carrusel CustomTkinter: onboarding → operación → carpeta → IA → preview → fin."""

from __future__ import annotations

import os
import sys
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

_MODE_LABELS = {"System": "Sistema", "Light": "Claro", "Dark": "Oscuro"}
_LABEL_TO_MODE = {v: k for k, v in _MODE_LABELS.items()}

_SLIDE_TITLES: dict[str, str] = {
    "loading": "Iniciando",
    "welcome": "Bienvenida",
    "objetivo": "Objetivo",
    "tut_organize": "Tutorial · Organizar",
    "tut_clean": "Tutorial · Eliminar",
    "tut_both": "Tutorial · Ambos",
    "choose_op": "Elegir operación",
    "folder": "Carpeta",
    "ai": "IA opcional",
    "preview": "Preview",
    "confirm": "Confirmación",
    "done": "Listo",
}

_LOADING_MS = 1200


def _has_groq_key() -> bool:
    return bool(os.environ.get("GROQ_API_KEY", "").strip())


def _find_splash_image() -> Path | None:
    """Busca splash.png junto al paquete, en assets del proyecto o en el bundle."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "assets" / "splash.png",  # .../Taxos/assets
        here.parents[2] / "assets" / "splash.png",
        Path.cwd() / "assets" / "splash.png",
    ]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.insert(0, Path(meipass) / "assets" / "splash.png")
    for path in candidates:
        if path.is_file():
            return path
    return None


class TaxosWizard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Taxos — organizar Descargas")
        self.minsize(480, 360)

        self.target = get_downloads_dir()
        self.do_organize = ctk.BooleanVar(value=True)
        self.do_clean = ctk.BooleanVar(value=False)
        self.use_ai = ctk.BooleanVar(value=False)
        self.slide_id = "loading"
        self._slide_history: list[str] = []
        self.move_actions: list[MoveAction] = []
        self.trash_candidates: list[TrashCandidate] = []
        self._wrap_labels: list[ctk.CTkLabel] = []
        self._result_message = "Operación terminada."
        self._footer_buttons: list[ctk.CTkButton] = []
        self._splash_image: ctk.CTkImage | None = None
        self._loading_job: str | None = None

        prefs = load_gui_prefs()
        self._appearance_mode = prefs["appearance_mode"]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer()
        self._center_window(720, 520)
        self.bind("<Configure>", self._on_resize)
        self._load_splash_image()
        self._show_slide("loading", push_history=False)

    def _center_window(self, width: int, height: int) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _load_splash_image(self) -> None:
        path = _find_splash_image()
        if path is None:
            return
        try:
            from PIL import Image

            img = Image.open(path)
            self._splash_image = ctk.CTkImage(
                light_image=img, dark_image=img, size=(240, 140)
            )
        except Exception:  # noqa: BLE001 — imagen opcional
            self._splash_image = None

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
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 16))
        self.footer.grid_columnconfigure(1, weight=1)

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

    def _clear_footer(self) -> None:
        for child in self.footer.winfo_children():
            child.destroy()
        self._footer_buttons.clear()

    def _footer_btn(
        self,
        text: str,
        command,
        *,
        primary: bool = False,
        side: str = "right",
        width: int = 130,
    ) -> ctk.CTkButton:
        kwargs: dict = {"text": text, "width": width, "command": command}
        if not primary:
            kwargs.update(
                {
                    "fg_color": "transparent",
                    "border_width": 1,
                    "text_color": ("gray20", "gray90"),
                }
            )
        btn = ctk.CTkButton(self.footer, **kwargs)
        if side == "left":
            btn.pack(side="left", padx=(0, 8))
        else:
            btn.pack(side="right", padx=(8, 0))
        self._footer_buttons.append(btn)
        return btn

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

    def _show_slide(self, slide_id: str, *, push_history: bool = True) -> None:
        if push_history and self.slide_id and self.slide_id != slide_id:
            self._slide_history.append(self.slide_id)
        self.slide_id = slide_id
        self._clear_body()
        self._clear_footer()
        self.step_label.configure(text=_SLIDE_TITLES.get(slide_id, slide_id))

        renderers = {
            "loading": self._slide_loading,
            "welcome": self._slide_welcome,
            "objetivo": self._slide_objetivo,
            "tut_organize": self._slide_tut_organize,
            "tut_clean": self._slide_tut_clean,
            "tut_both": self._slide_tut_both,
            "choose_op": self._slide_choose_op,
            "folder": self._slide_folder,
            "ai": self._slide_ai,
            "preview": self._slide_preview,
            "confirm": self._slide_confirm,
            "done": self._slide_done,
        }
        renderers[slide_id]()

    def _go_back(self) -> None:
        if not self._slide_history:
            return
        prev = self._slide_history.pop()
        self._show_slide(prev, push_history=False)

    # --- Slides ---

    def _slide_loading(self) -> None:
        if self._splash_image is not None:
            ctk.CTkLabel(self.body, image=self._splash_image, text="").pack(
                pady=(24, 12)
            )
        self._section_title("Iniciando Taxos…")
        self._section_subtitle("Preparando el asistente. Un momento.")
        bar = ctk.CTkProgressBar(self.body, mode="indeterminate", width=280)
        bar.pack(pady=(8, 24))
        bar.start()
        if self._loading_job is not None:
            try:
                self.after_cancel(self._loading_job)
            except Exception:  # noqa: BLE001
                pass
        self._loading_job = self.after(
            _LOADING_MS, lambda: self._show_slide("welcome", push_history=False)
        )

    def _slide_welcome(self) -> None:
        self._section_title("Bienvenida")
        self._section_subtitle(
            "Taxos te ayuda a organizar y limpiar tu carpeta Descargas "
            "con un preview antes de aplicar cambios."
        )
        self._footer_btn("Atrás", self._go_back, side="left")
        self._footer_btn("Siguiente", lambda: self._show_slide("objetivo"), primary=True)

    def _slide_objetivo(self) -> None:
        self._section_title("Objetivo")
        self._section_subtitle(
            "Puedes organizar archivos por categoría, eliminar basura segura "
            "(tmp, vacíos, locks) o ambas cosas. Elige si quieres un tutorial breve."
        )
        self._footer_btn("Atrás", self._go_back, side="left")
        self._footer_btn(
            "Omitir tutorial",
            lambda: self._show_slide("choose_op"),
            side="right",
            width=150,
        )
        self._footer_btn(
            "Ver tutorial",
            lambda: self._show_slide("tut_organize"),
            primary=True,
            width=140,
        )

    def _slide_tut_organize(self) -> None:
        self._section_title("Organizar")
        self._section_subtitle(
            "Mueve archivos de la raíz de Descargas a subcarpetas según su tipo "
            "(imágenes, documentos, instaladores, etc.)."
        )
        self._footer_btn("Atrás", self._go_back, side="left")
        self._footer_btn(
            "Siguiente", lambda: self._show_slide("tut_clean"), primary=True
        )

    def _slide_tut_clean(self) -> None:
        self._section_title("Eliminar basura")
        self._section_subtitle(
            "Envía a la papelera archivos temporales, vacíos o locks de forma segura. "
            "No borra de forma permanente."
        )
        self._footer_btn("Atrás", self._go_back, side="left")
        self._footer_btn(
            "Siguiente", lambda: self._show_slide("tut_both"), primary=True
        )

    def _slide_tut_both(self) -> None:
        self._section_title("Organizar y eliminar")
        self._section_subtitle(
            "También puedes combinar ambas acciones en una sola pasada. "
            "Siempre verás un preview antes de confirmar."
        )
        self._footer_btn("Atrás", self._go_back, side="left")
        self._footer_btn(
            "Elegir operación",
            lambda: self._show_slide("choose_op"),
            primary=True,
            width=160,
        )

    def _slide_choose_op(self) -> None:
        self._section_title("Elegir operación")
        self._section_subtitle("¿Qué quieres hacer en esta pasada?")

        def pick(organize: bool, clean: bool) -> None:
            self.do_organize.set(organize)
            self.do_clean.set(clean)
            self._show_slide("folder")

        for text, org, clean in (
            ("Organizar", True, False),
            ("Eliminar", False, True),
            ("Ambos", True, True),
        ):
            ctk.CTkButton(
                self.body,
                text=text,
                height=40,
                command=lambda o=org, c=clean: pick(o, c),
            ).pack(fill="x", pady=6)

        self._footer_btn("Atrás", self._go_back, side="left")

    def _slide_folder(self) -> None:
        self._section_title("Carpeta")
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

        self._footer_btn("Atrás", self._go_back, side="left")
        self._footer_btn("Siguiente", self._from_folder_next, primary=True)

    def _browse(self) -> None:
        chosen = filedialog.askdirectory(initialdir=str(self.target))
        if chosen:
            self.target = Path(chosen)
            self.path_label.configure(text=str(self.target))

    def _from_folder_next(self) -> None:
        if not self.target.is_dir():
            messagebox.showerror("Taxos", f"No existe la carpeta:\n{self.target}")
            return
        self._show_slide("ai")

    def _slide_ai(self) -> None:
        self._section_title("¿Usar IA?")
        has_key = _has_groq_key()
        if has_key:
            hint = (
                "Se detectó GROQ_API_KEY. La IA solo ve nombres de archivo, "
                "nunca el contenido. Puedes omitir y usar las reglas locales."
            )
        else:
            hint = (
                "No hay GROQ_API_KEY configurada. Puedes omitir y usar la lógica "
                "predeterminada del software, o configurar la clave y volver."
            )
        self._section_subtitle(hint)

        self._footer_btn("Atrás", self._go_back, side="left")
        self._footer_btn("Omitir", self._ai_omit, width=120)
        self._footer_btn("Usar IA", self._ai_use, primary=True, width=120)

    def _ai_omit(self) -> None:
        self.use_ai.set(False)
        self._show_slide("preview")

    def _ai_use(self) -> None:
        if not _has_groq_key():
            messagebox.showinfo(
                "Taxos",
                "No hay GROQ_API_KEY. Configúrala en el entorno o en un archivo .env, "
                "o pulsa Omitir para usar las reglas locales.",
            )
            return
        self.use_ai.set(True)
        self._show_slide("preview")

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

    def _slide_preview(self) -> None:
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

        if not self.move_actions and not self.trash_candidates:
            lines.append("Nada que hacer en esta carpeta con la operación elegida.")

        box = ctk.CTkTextbox(self.body, wrap="word", height=240)
        box.pack(fill="both", expand=True, pady=(4, 0))
        box.insert("1.0", "\n".join(lines) if lines else "(vacío)")
        box.configure(state="disabled")

        self._footer_btn("Atrás", self._go_back, side="left")
        self._footer_btn(
            "Continuar",
            lambda: self._show_slide("confirm"),
            primary=True,
            width=130,
        )

    def _slide_confirm(self) -> None:
        self._section_title("Confirmación")
        summary = (
            f"Se van a mover {len(self.move_actions)} archivo(s) "
            f"y enviar {len(self.trash_candidates)} a la papelera.\n\n"
            "¿Confirmas aplicar el plan?"
        )
        self._section_subtitle(summary)

        self._footer_btn(
            "No",
            lambda: self._show_slide("preview"),
            side="left",
            width=100,
        )
        self._footer_btn("Sí, aplicar", self._confirm_apply, primary=True, width=140)

    def _confirm_apply(self) -> None:
        if not self.do_organize.get() and not self.do_clean.get():
            messagebox.showinfo("Taxos", "No hay operación seleccionada.")
            self._show_slide("choose_op")
            return
        if not self.move_actions and not self.trash_candidates:
            messagebox.showinfo("Taxos", "No hay acciones en el plan.")
            self._show_slide("preview")
            return

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
        self._show_slide("done")

    def _slide_done(self) -> None:
        self._section_title("Listo")
        self._section_subtitle(self._result_message)
        self._footer_btn("Cerrar", self.destroy, side="left", width=110)
        self._footer_btn(
            "Realizar otra operación",
            self._restart_operation,
            primary=True,
            width=200,
        )

    def _restart_operation(self) -> None:
        self.move_actions = []
        self.trash_candidates = []
        self.use_ai.set(False)
        self._result_message = "Operación terminada."
        self._slide_history.clear()
        self._show_slide("choose_op", push_history=False)


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
