const SLIDE_TITLES = {
  loading: "Iniciando",
  welcome: "Bienvenida",
  objetivo: "Objetivo",
  tut_organize: "Tutorial · Organizar",
  tut_clean: "Tutorial · Eliminar",
  tut_both: "Tutorial · Ambos",
  choose_op: "Elegir operación",
  folder: "Carpeta",
  ai: "IA opcional",
  preview: "Preview",
  confirm: "Confirmación",
  done: "Listo",
};

const LOADING_MS = 1200;

function btn(label, { primary = false, danger = false } = {}) {
  const base =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-sky-500/40";
  if (primary) {
    return `${base} bg-sky-600 text-white hover:bg-sky-500`;
  }
  if (danger) {
    return `${base} border border-zinc-300 bg-transparent text-zinc-800 hover:bg-zinc-100 dark:border-zinc-600 dark:text-zinc-100 dark:hover:bg-zinc-800`;
  }
  return `${base} border border-zinc-300 bg-transparent text-zinc-800 hover:bg-zinc-100 dark:border-zinc-600 dark:text-zinc-100 dark:hover:bg-zinc-800`;
}

function waitForApi(timeoutMs = 8000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const tick = () => {
      if (window.pywebview?.api) {
        resolve(window.pywebview.api);
        return;
      }
      if (Date.now() - start > timeoutMs) {
        reject(new Error("PyWebView API no disponible"));
        return;
      }
      setTimeout(tick, 50);
    };
    tick();
  });
}

export function createApp(root) {
  const state = {
    slideId: "loading",
    history: [],
    theme: "System",
    folder: "",
    hasGroqKey: false,
    doOrganize: true,
    doClean: false,
    useAi: false,
    preview: { moveCount: 0, trashCount: 0, lines: [] },
    resultMessage: "Operación terminada.",
    busy: false,
    error: "",
    api: null,
  };

  function applyTheme(mode) {
    state.theme = mode;
    const dark =
      mode === "Dark" ||
      (mode === "System" &&
        window.matchMedia?.("(prefers-color-scheme: dark)").matches);
    document.documentElement.classList.toggle("dark", Boolean(dark));
  }

  function go(slideId, { push = true } = {}) {
    if (push && state.slideId && state.slideId !== slideId) {
      state.history.push(state.slideId);
    }
    state.slideId = slideId;
    state.error = "";
    render();
  }

  function back() {
    if (!state.history.length) return;
    state.slideId = state.history.pop();
    state.error = "";
    render();
  }

  async function withApi(fn) {
    if (!state.api) {
      state.error = "API no lista.";
      render();
      return;
    }
    state.busy = true;
    state.error = "";
    render();
    try {
      return await fn(state.api);
    } catch (err) {
      state.error = String(err?.message || err);
      render();
      return null;
    } finally {
      state.busy = false;
      render();
    }
  }

  function shell(title, bodyHtml, footerHtml) {
    const themes = ["System", "Light", "Dark"];
    const themeLabels = { System: "Sistema", Light: "Claro", Dark: "Oscuro" };
    return `
      <header class="mb-4 flex flex-wrap items-center gap-3">
        <h1 class="text-2xl font-bold tracking-tight">Taxos</h1>
        <p class="text-sm text-zinc-500 dark:text-zinc-400">${title}</p>
        <div class="ml-auto flex rounded-lg border border-zinc-300 p-0.5 dark:border-zinc-600">
          ${themes
            .map(
              (m) => `
            <button type="button" data-theme="${m}"
              class="rounded-md px-2.5 py-1 text-xs ${
                state.theme === m
                  ? "bg-sky-600 text-white"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
              }">${themeLabels[m]}</button>`
            )
            .join("")}
        </div>
      </header>
      <main class="flex-1">${bodyHtml}</main>
      ${
        state.error
          ? `<p class="mt-3 text-sm text-red-600 dark:text-red-400">${state.error}</p>`
          : ""
      }
      <footer class="mt-6 flex flex-wrap items-center gap-2">${footerHtml}</footer>
    `;
  }

  function titleBlock(h, p) {
    return `
      <h2 class="text-xl font-semibold">${h}</h2>
      <p class="mt-2 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">${p}</p>
    `;
  }

  function renderSlide() {
    const id = state.slideId;
    const t = SLIDE_TITLES[id] || id;

    if (id === "loading") {
      return shell(
        t,
        `
        <div class="flex flex-col items-center py-10 text-center">
          <img src="./splash.png" alt="" class="mb-6 h-28 w-auto opacity-90" onerror="this.style.display='none'" />
          ${titleBlock("Iniciando Taxos…", "Preparando el asistente. Un momento.")}
          <div class="mt-8 h-1.5 w-64 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
            <div class="taxos-progress-bar h-full w-1/3 rounded-full bg-sky-600"></div>
          </div>
        </div>
        `,
        ""
      );
    }

    if (id === "welcome") {
      return shell(
        t,
        titleBlock(
          "Bienvenida",
          "Taxos te ayuda a organizar y limpiar tu carpeta Descargas con un preview antes de aplicar cambios."
        ),
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-go="objetivo" class="${btn("", { primary: true })}">Siguiente</button>
        `
      );
    }

    if (id === "objetivo") {
      return shell(
        t,
        titleBlock(
          "Objetivo",
          "Puedes organizar archivos por categoría, eliminar basura segura (tmp, vacíos, locks) o ambas cosas. Elige si quieres un tutorial breve."
        ),
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto flex flex-wrap gap-2">
          <button type="button" data-go="choose_op" class="${btn("")}">Omitir tutorial</button>
          <button type="button" data-go="tut_organize" class="${btn("", { primary: true })}">Ver tutorial</button>
        </div>
        `
      );
    }

    if (id === "tut_organize") {
      return shell(
        t,
        titleBlock(
          "Organizar",
          "Mueve archivos de la raíz de Descargas a subcarpetas según su tipo (imágenes, documentos, instaladores, etc.)."
        ),
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-go="tut_clean" class="${btn("", { primary: true })}">Siguiente</button>
        `
      );
    }

    if (id === "tut_clean") {
      return shell(
        t,
        titleBlock(
          "Eliminar basura",
          "Envía a la papelera archivos temporales, vacíos o locks de forma segura. No borra de forma permanente."
        ),
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-go="tut_both" class="${btn("", { primary: true })}">Siguiente</button>
        `
      );
    }

    if (id === "tut_both") {
      return shell(
        t,
        titleBlock(
          "Organizar y eliminar",
          "También puedes combinar ambas acciones en una sola pasada. Siempre verás un preview antes de confirmar."
        ),
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-go="choose_op" class="${btn("", { primary: true })}">Elegir operación</button>
        `
      );
    }

    if (id === "choose_op") {
      return shell(
        t,
        `
        ${titleBlock("Elegir operación", "¿Qué quieres hacer en esta pasada?")}
        <div class="mt-6 grid gap-3">
          <button type="button" data-op="organize" class="${btn("", { primary: true })} w-full py-3">Organizar</button>
          <button type="button" data-op="clean" class="${btn("", { primary: true })} w-full py-3">Eliminar</button>
          <button type="button" data-op="both" class="${btn("", { primary: true })} w-full py-3">Ambos</button>
        </div>
        `,
        `<button type="button" data-action="back" class="${btn("")}">Atrás</button>`
      );
    }

    if (id === "folder") {
      return shell(
        t,
        `
        ${titleBlock("Carpeta", "Por defecto se usa tu carpeta Descargas.")}
        <div class="mt-4 flex items-center gap-3 rounded-xl border border-zinc-200 bg-zinc-100/80 p-3 dark:border-zinc-700 dark:bg-zinc-900">
          <p class="min-w-0 flex-1 break-all text-sm">${state.folder || "—"}</p>
          <button type="button" data-action="browse" class="${btn("")}">Examinar…</button>
        </div>
        `,
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="folder-next" class="${btn("", { primary: true })}">Siguiente</button>
        `
      );
    }

    if (id === "ai") {
      const hint = state.hasGroqKey
        ? "Se detectó GROQ_API_KEY. La IA solo ve nombres de archivo, nunca el contenido. Puedes omitir y usar las reglas locales."
        : "No hay GROQ_API_KEY configurada. Puedes omitir y usar la lógica predeterminada del software, o configurar la clave y volver.";
      return shell(
        t,
        titleBlock("¿Usar IA?", hint),
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto flex gap-2">
          <button type="button" data-action="ai-omit" class="${btn("")}">Omitir</button>
          <button type="button" data-action="ai-use" class="${btn("", { primary: true })}">Usar IA</button>
        </div>
        `
      );
    }

    if (id === "preview") {
      const lines = state.preview.lines?.length
        ? state.preview.lines.join("\n")
        : "Nada que hacer en esta carpeta con la operación elegida.";
      return shell(
        t,
        `
        ${titleBlock("Preview del plan", "")}
        <div class="mb-3 flex gap-4 text-sm font-semibold">
          ${state.doOrganize ? `<span>Movimientos: ${state.preview.moveCount}</span>` : ""}
          ${state.doClean ? `<span>A papelera: ${state.preview.trashCount}</span>` : ""}
        </div>
        <pre class="max-h-64 overflow-auto rounded-xl border border-zinc-200 bg-white p-3 text-xs leading-relaxed dark:border-zinc-700 dark:bg-zinc-900">${escapeHtml(lines)}</pre>
        `,
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-go="confirm" class="${btn("", { primary: true })}" ${state.busy ? "disabled" : ""}>Continuar</button>
        `
      );
    }

    if (id === "confirm") {
      return shell(
        t,
        titleBlock(
          "Confirmación",
          `Se van a mover ${state.preview.moveCount} archivo(s) y enviar ${state.preview.trashCount} a la papelera. ¿Confirmas aplicar el plan?`
        ),
        `
        <button type="button" data-go="preview" class="${btn("")}">No</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="apply" class="${btn("", { primary: true })}" ${state.busy ? "disabled" : ""}>Sí, aplicar</button>
        `
      );
    }

    if (id === "done") {
      return shell(
        t,
        titleBlock("Listo", state.resultMessage),
        `
        <button type="button" data-action="close" class="${btn("")}">Cerrar</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="again" class="${btn("", { primary: true })}">Realizar otra operación</button>
        `
      );
    }

    return shell(t, "<p>Slide desconocido.</p>", "");
  }

  function escapeHtml(text) {
    return String(text)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function bind() {
    root.querySelectorAll("[data-theme]").forEach((el) => {
      el.addEventListener("click", async () => {
        const mode = el.getAttribute("data-theme");
        applyTheme(mode);
        await withApi((api) => api.set_theme(mode));
      });
    });

    root.querySelectorAll("[data-go]").forEach((el) => {
      el.addEventListener("click", () => {
        go(el.getAttribute("data-go"));
      });
    });

    root.querySelector('[data-action="back"]')?.addEventListener("click", back);

    root.querySelectorAll("[data-op]").forEach((el) => {
      el.addEventListener("click", async () => {
        const kind = el.getAttribute("data-op");
        await withApi((api) => api.set_operation(kind));
        if (kind === "organize") {
          state.doOrganize = true;
          state.doClean = false;
        } else if (kind === "clean") {
          state.doOrganize = false;
          state.doClean = true;
        } else {
          state.doOrganize = true;
          state.doClean = true;
        }
        go("folder");
      });
    });

    root.querySelector('[data-action="browse"]')?.addEventListener("click", async () => {
      const path = await withApi((api) => api.browse_folder());
      if (path) {
        state.folder = path;
        render();
      }
    });

    root.querySelector('[data-action="folder-next"]')?.addEventListener("click", async () => {
      const ok = await withApi((api) => api.set_folder(state.folder));
      if (ok?.ok === false) {
        state.error = ok.error || "Carpeta inválida";
        render();
        return;
      }
      if (ok !== null) go("ai");
    });

    root.querySelector('[data-action="ai-omit"]')?.addEventListener("click", async () => {
      await withApi((api) => api.set_use_ai(false));
      state.useAi = false;
      await loadPreview();
      go("preview");
    });

    root.querySelector('[data-action="ai-use"]')?.addEventListener("click", async () => {
      const res = await withApi((api) => api.set_use_ai(true));
      if (res?.ok === false) {
        state.error = res.error || "No hay GROQ_API_KEY";
        render();
        return;
      }
      state.useAi = true;
      await loadPreview();
      go("preview");
    });

    root.querySelector('[data-action="apply"]')?.addEventListener("click", async () => {
      const res = await withApi((api) => api.apply_plan());
      if (!res) return;
      if (res.ok === false) {
        state.error = res.error || "No se pudo aplicar";
        render();
        return;
      }
      state.resultMessage = res.message || "Operación terminada.";
      go("done");
    });

    root.querySelector('[data-action="close"]')?.addEventListener("click", async () => {
      await withApi((api) => api.close_app());
    });

    root.querySelector('[data-action="again"]')?.addEventListener("click", async () => {
      await withApi((api) => api.reset_operation());
      state.useAi = false;
      state.preview = { moveCount: 0, trashCount: 0, lines: [] };
      state.history = [];
      go("choose_op", { push: false });
    });
  }

  async function loadPreview() {
    const res = await withApi((api) => api.build_preview());
    if (res) {
      state.preview = {
        moveCount: res.move_count ?? 0,
        trashCount: res.trash_count ?? 0,
        lines: res.lines || [],
      };
    }
  }

  function render() {
    root.innerHTML = renderSlide();
    bind();
  }

  async function boot() {
    render();
    setTimeout(() => {
      if (state.slideId === "loading") go("welcome", { push: false });
    }, LOADING_MS);

    try {
      state.api = await waitForApi();
      const s = await state.api.get_state();
      state.folder = s.folder || "";
      state.hasGroqKey = Boolean(s.has_groq_key);
      applyTheme(s.theme || "System");
      render();
    } catch (err) {
      state.error = String(err.message || err);
      render();
    }
  }

  boot();
}
