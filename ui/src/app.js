const LOADING_MS = 1200;

const ORG_METHODS = [
  {
    id: "extension",
    title: "Por extensión",
    description: "Clasifica según el tipo de archivo (.pdf, .jpg, .docx, .zip…).",
    enabled: true,
  },
  {
    id: "date",
    title: "Por fecha",
    description: "Crea carpetas por año, mes o día.",
    enabled: false,
  },
  {
    id: "name",
    title: "Por nombre",
    description: "Busca palabras en el nombre del archivo.",
    enabled: false,
  },
  {
    id: "content",
    title: "Por contenido",
    description: "Abre el archivo y analiza su contenido.",
    enabled: false,
  },
  {
    id: "tags",
    title: "Por etiquetas",
    description: "No mueve archivos; los categoriza con etiquetas.",
    enabled: false,
  },
  {
    id: "duplicates",
    title: "Por duplicados",
    description: "Detecta y elimina archivos repetidos.",
    enabled: false,
  },
  {
    id: "projects",
    title: "Por proyectos",
    description: "Agrupa archivos relacionados.",
    enabled: false,
  },
  {
    id: "rules",
    title: "Por reglas personalizadas",
    description: "Si ocurre X, haz Y.",
    enabled: false,
  },
];

function btn(label, { primary = false, danger = false, muted = false } = {}) {
  const base =
    "inline-flex items-center justify-center rounded-md px-5 py-2.5 text-sm font-medium tracking-wide transition focus:outline-none focus:ring-2 focus:ring-stone-400/40 disabled:cursor-not-allowed disabled:opacity-45";
  if (primary) {
    return `${base} bg-stone-900 text-stone-50 hover:bg-stone-800`;
  }
  if (danger) {
    return `${base} border border-stone-300/80 bg-transparent text-stone-800 hover:bg-stone-900/5`;
  }
  if (muted) {
    return `${base} border border-stone-200 bg-stone-100/80 text-stone-400`;
  }
  return `${base} border border-stone-300/70 bg-transparent text-stone-700 hover:bg-stone-900/[0.04]`;
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

function iconFolder() {
  return `<svg class="h-5 w-5 shrink-0 text-stone-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7.5A1.5 1.5 0 0 1 4.5 6h4.379a1.5 1.5 0 0 1 1.06.44l1.122 1.12A1.5 1.5 0 0 0 12.121 8H19.5A1.5 1.5 0 0 1 21 9.5v8a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5v-10Z"/></svg>`;
}

function iconTrash() {
  return `<svg class="h-5 w-5 shrink-0 text-stone-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673A2.25 2.25 0 0 1 15.916 21.75H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"/></svg>`;
}

function iconChevron(open) {
  return `<svg class="h-4 w-4 shrink-0 text-stone-400 transition ${open ? "rotate-180" : ""}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5"/></svg>`;
}

export function createApp(root) {
  const state = {
    slideId: "loading",
    history: [],
    theme: "Light",
    folder: "",
    hasGroqKey: false,
    doOrganize: true,
    doClean: false,
    useAi: false,
    orgMethod: null,
    preview: { moveCount: 0, trashCount: 0, groups: [], lines: [] },
    expandedGroup: null,
    resultMessage: "Operación terminada.",
    busy: false,
    error: "",
    api: null,
  };

  function applyTheme(_mode) {
    state.theme = "Light";
    document.documentElement.classList.remove("dark");
  }

  function go(slideId, { push = true } = {}) {
    if (push && state.slideId && state.slideId !== slideId) {
      state.history.push(state.slideId);
    }
    state.slideId = slideId;
    state.error = "";
    if (slideId !== "preview") {
      state.expandedGroup = null;
    }
    render({ animate: true });
  }

  function back() {
    if (!state.history.length) return;
    state.slideId = state.history.pop();
    state.error = "";
    if (state.slideId !== "preview") {
      state.expandedGroup = null;
    }
    render({ animate: true });
  }

  function backToOperations() {
    state.history = [];
    state.expandedGroup = null;
    state.orgMethod = null;
    go("choose_op", { push: false });
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

  function shell(bodyHtml, footerHtml, { bare = false } = {}) {
    if (bare) {
      return `
        <main class="flex min-h-screen flex-1 flex-col">${bodyHtml}</main>
        ${
          state.error
            ? `<p class="px-6 text-sm text-red-700/90">${state.error}</p>`
            : ""
        }
      `;
    }
    return `
      <div class="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-5">
        <main class="flex flex-1 flex-col">${bodyHtml}</main>
        ${
          state.error
            ? `<p class="mt-3 text-sm text-red-700/90">${state.error}</p>`
            : ""
        }
        ${
          footerHtml
            ? `<footer class="mt-8 flex flex-wrap items-center gap-2">${footerHtml}</footer>`
            : ""
        }
      </div>
    `;
  }

  function heroSlide({ title, imageSrc, subtitle, footerHtml }) {
    return `
      <div class="flex min-h-screen w-full flex-col bg-white">
        <div class="px-6 pt-10 text-center sm:px-10 sm:pt-12">
          <h2 class="font-display text-3xl font-medium tracking-tight text-stone-900 sm:text-4xl">${title}</h2>
        </div>
        <div class="flex flex-1 items-center justify-center px-6 py-4">
          <img src="${imageSrc}" alt="" class="taxos-hero-img drop-shadow-sm" onerror="this.style.display='none'" />
        </div>
        <div class="px-6 pb-4 text-center sm:px-10">
          <p class="mx-auto max-w-lg text-sm font-light leading-relaxed text-stone-700 sm:text-base">${subtitle}</p>
        </div>
        ${
          footerHtml
            ? `<footer class="flex flex-wrap items-center gap-2 px-6 pb-8 pt-2 sm:px-10">${footerHtml}</footer>`
            : ""
        }
        ${
          state.error
            ? `<p class="px-6 pb-4 text-sm text-red-700/90">${state.error}</p>`
            : ""
        }
      </div>
    `;
  }

  function titleBlock(h, p) {
    return `
      <h2 class="font-display text-2xl font-medium tracking-tight text-stone-900">${h}</h2>
      <p class="mt-2 text-sm font-light leading-relaxed text-stone-600">${p}</p>
    `;
  }

  function renderSlide() {
    const id = state.slideId;

    if (id === "loading") {
      return shell(
        `
        <div class="flex flex-1 flex-col items-center justify-center py-10 text-center">
          <img src="./splash.png" alt="" class="mb-6 h-24 w-auto opacity-90" onerror="this.style.display='none'" />
          <h2 class="font-display text-2xl font-medium text-stone-900">Iniciando Taxos…</h2>
          <p class="mt-2 text-sm font-light text-stone-500">Preparando el asistente.</p>
          <div class="mt-10 h-px w-48 overflow-hidden bg-stone-300/80">
            <div class="taxos-progress-bar h-full w-1/3 bg-stone-800"></div>
          </div>
        </div>
        `,
        "",
        { bare: true }
      );
    }

    if (id === "welcome") {
      return heroSlide({
        title: "Bienvenido/a",
        imageSrc: "./InicioPortada.svg",
        subtitle: "Organiza y Limpia de Archivos Basura",
        footerHtml: `
          <div class="ml-auto"></div>
          <button type="button" data-go="objetivo" class="${btn("", { primary: true })}">Comenzar</button>
        `,
      });
    }

    if (id === "objetivo") {
      return heroSlide({
        title: "Objetivo",
        imageSrc: "./InicioPortada.svg",
        subtitle:
          "Puedes organizar archivos por categoría, eliminar basura segura (tmp, vacíos, locks) o ambas cosas. Elige si quieres un tutorial breve.",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <div class="ml-auto flex flex-wrap gap-2">
            <button type="button" data-go="choose_op" class="${btn("")}">Omitir tutorial</button>
            <button type="button" data-go="tut_organize" class="${btn("", { primary: true })}">Ver tutorial</button>
          </div>
        `,
      });
    }

    if (id === "tut_organize") {
      return heroSlide({
        title: "Organizar",
        imageSrc: "./ExtensionDeArchivos.svg",
        subtitle:
          "Mueve archivos de la raíz de Descargas a subcarpetas según su tipo (imágenes, documentos, instaladores, etc.).",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <div class="ml-auto"></div>
          <button type="button" data-go="tut_clean" class="${btn("", { primary: true })}">Siguiente</button>
        `,
      });
    }

    if (id === "tut_clean") {
      return heroSlide({
        title: "Eliminar basura",
        imageSrc: "./ExtensionDeArchivos.svg",
        subtitle:
          "Envía a la papelera archivos temporales, vacíos o locks de forma segura. No borra de forma permanente.",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <div class="ml-auto"></div>
          <button type="button" data-go="tut_both" class="${btn("", { primary: true })}">Siguiente</button>
        `,
      });
    }

    if (id === "tut_both") {
      return heroSlide({
        title: "Organizar y eliminar",
        imageSrc: "./ExtensionDeArchivos.svg",
        subtitle:
          "También puedes combinar ambas acciones en una sola pasada. Siempre verás un preview antes de confirmar.",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <div class="ml-auto"></div>
          <button type="button" data-go="choose_op" class="${btn("", { primary: true })}">Elegir operación</button>
        `,
      });
    }

    if (id === "choose_op") {
      const cell =
        "flex min-h-[5.5rem] flex-col items-center justify-center rounded-lg border border-stone-300/60 bg-white px-3 py-4 text-sm font-medium tracking-wide text-stone-800 transition hover:border-stone-400 hover:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-400/30";
      const cellMuted =
        "flex min-h-[5.5rem] cursor-not-allowed flex-col items-center justify-center rounded-lg border border-stone-200/80 bg-stone-100/50 px-3 py-4 text-sm font-medium tracking-wide text-stone-400";
      return shell(
        `
        ${titleBlock("Elegir operación", "¿Qué quieres hacer en esta pasada?")}
        <div class="mt-8 grid grid-cols-2 gap-3">
          <button type="button" data-op="organize" class="${cell}">Organizar</button>
          <button type="button" data-op="clean" class="${cell}">Eliminar</button>
          <button type="button" data-op="both" class="${cell}">Ambos</button>
          <button type="button" disabled class="${cellMuted}" title="Próximamente">Buscar</button>
        </div>
        `,
        `<button type="button" data-action="back" class="${btn("")}">Atrás</button>`
      );
    }

    if (id === "folder") {
      return shell(
        `
        ${titleBlock("Carpeta", "Por defecto se usa tu carpeta Descargas.")}
        <div class="mt-6 flex items-center gap-3 border-b border-stone-300/70 py-3">
          <p class="min-w-0 flex-1 break-all text-sm font-light text-stone-700">${state.folder || "—"}</p>
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

    if (id === "org_method") {
      const cellOn =
        "flex min-h-[7rem] flex-col items-start justify-center rounded-lg border border-stone-300/70 bg-white px-4 py-4 text-left transition hover:border-stone-500 hover:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-400/30";
      const cellOff =
        "flex min-h-[7rem] cursor-not-allowed flex-col items-start justify-center rounded-lg border border-stone-200/80 bg-stone-50/80 px-4 py-4 text-left opacity-60";
      const cards = ORG_METHODS.map((m) => {
        if (m.enabled) {
          return `
            <button type="button" data-org-method="${m.id}" class="${cellOn}">
              <span class="font-display text-lg font-medium text-stone-900">${m.title}</span>
              <span class="mt-2 text-xs font-light leading-relaxed text-stone-500">${m.description}</span>
            </button>`;
        }
        return `
          <button type="button" disabled class="${cellOff}" title="Próximamente">
            <span class="font-display text-lg font-medium text-stone-400">${m.title}</span>
            <span class="mt-2 text-xs font-light leading-relaxed text-stone-400">${m.description}</span>
          </button>`;
      }).join("");

      return shell(
        `
        ${titleBlock("Forma de organizar", "Elige cómo clasificar los archivos. Luego verás el preview por carpetas.")}
        <div class="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">${cards}</div>
        `,
        `<button type="button" data-action="back" class="${btn("")}">Atrás</button>`
      );
    }

    if (id === "preview") {
      const groups = state.preview.groups || [];
      const listHtml = groups.length
        ? `<ul class="mt-6 divide-y divide-stone-300/50 border-y border-stone-300/50">
            ${groups
              .map((g) => {
                const open = state.expandedGroup === g.name;
                const files = g.files || [];
                const filesHtml = open
                  ? `<ul class="max-h-40 overflow-y-auto border-t border-stone-200/80 bg-stone-50/80 px-3 py-2 pl-11">
                      ${
                        files.length
                          ? files
                              .map(
                                (f) => `
                          <li class="flex items-center justify-between gap-3 py-1.5 text-xs text-stone-600">
                            <span class="min-w-0 truncate font-light">${escapeHtml(f.name)}</span>
                            <span class="shrink-0 text-stone-400">${escapeHtml(f.size_label || "")}</span>
                          </li>`
                              )
                              .join("")
                          : `<li class="py-1.5 text-xs font-light text-stone-400">Sin archivos</li>`
                      }
                    </ul>`
                  : "";
                return `
              <li>
                <button type="button" data-expand="${escapeHtml(g.name)}"
                  class="flex w-full items-center gap-3 py-3.5 text-left transition hover:bg-stone-50/80 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-stone-300/50">
                  ${g.kind === "trash" ? iconTrash() : iconFolder()}
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-medium text-stone-900">${escapeHtml(g.name)}</p>
                    <p class="mt-0.5 text-xs font-light text-stone-500">${g.count} archivo${g.count === 1 ? "" : "s"} · ${escapeHtml(g.size_label || "")}</p>
                  </div>
                  ${iconChevron(open)}
                </button>
                ${filesHtml}
              </li>`;
              })
              .join("")}
          </ul>`
        : `<p class="mt-8 text-sm font-light text-stone-500">Nada que hacer en esta carpeta con la operación elegida.</p>`;

      return shell(
        `
        ${titleBlock("Preview", "Resumen por carpeta antes de aplicar. Pulsa una carpeta para ver los archivos.")}
        ${listHtml}
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
        titleBlock(
          "Confirmación",
          `Se van a mover ${state.preview.moveCount} archivo(s) y enviar ${state.preview.trashCount} a la papelera. ¿Confirmas aplicar el plan?`
        ),
        `
        <button type="button" data-action="confirm-no" class="${btn("")}">No</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="apply" class="${btn("", { primary: true })}" ${state.busy ? "disabled" : ""}>Sí, aplicar</button>
        `
      );
    }

    if (id === "done") {
      return shell(
        titleBlock("Listo", state.resultMessage),
        `
        <button type="button" data-action="close" class="${btn("")}">Cerrar</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="again" class="${btn("", { primary: true })}">Realizar otra operación</button>
        `
      );
    }

    return shell(`<p class="text-sm text-stone-600">Slide desconocido.</p>`, "");
  }

  function escapeHtml(text) {
    return String(text)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function bind() {
    root.querySelectorAll("[data-go]").forEach((el) => {
      el.addEventListener("click", () => {
        go(el.getAttribute("data-go"));
      });
    });

    root.querySelector('[data-action="back"]')?.addEventListener("click", back);

    root.querySelector('[data-action="confirm-no"]')?.addEventListener("click", () => {
      go("preview", { push: false });
    });

    root.querySelectorAll("[data-expand]").forEach((el) => {
      el.addEventListener("click", () => {
        const name = el.getAttribute("data-expand");
        state.expandedGroup = state.expandedGroup === name ? null : name;
        render({ animate: false });
      });
    });

    root.querySelectorAll("[data-org-method]").forEach((el) => {
      el.addEventListener("click", async () => {
        const method = el.getAttribute("data-org-method");
        state.orgMethod = method;
        state.useAi = false;
        await withApi((api) => api.set_use_ai(false));
        await loadPreview();
        go("preview");
      });
    });

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
        state.orgMethod = null;
        go("folder");
      });
    });

    root.querySelector('[data-action="browse"]')?.addEventListener("click", async () => {
      const path = await withApi((api) => api.browse_folder());
      if (path) {
        state.folder = path;
        render({ animate: false });
      }
    });

    root.querySelector('[data-action="folder-next"]')?.addEventListener("click", async () => {
      const ok = await withApi((api) => api.set_folder(state.folder));
      if (ok?.ok === false) {
        state.error = ok.error || "Carpeta inválida";
        render({ animate: false });
        return;
      }
      if (ok === null) return;
      state.useAi = false;
      await withApi((api) => api.set_use_ai(false));
      if (state.doOrganize) {
        go("org_method");
      } else {
        await loadPreview();
        go("preview");
      }
    });

    root.querySelector('[data-action="apply"]')?.addEventListener("click", async () => {
      const res = await withApi((api) => api.apply_plan());
      if (!res) return;
      if (res.ok === false) {
        state.error = res.error || "No se pudo aplicar";
        render({ animate: false });
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
      state.orgMethod = null;
      state.preview = { moveCount: 0, trashCount: 0, groups: [], lines: [] };
      state.expandedGroup = null;
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
        groups: res.groups || [],
        lines: res.lines || [],
      };
      state.expandedGroup = null;
    }
  }

  function render({ animate = false } = {}) {
    root.innerHTML = renderSlide();
    bind();
    if (animate) {
      const target = root.firstElementChild;
      if (target) {
        target.classList.remove("taxos-slide-enter");
        void target.offsetWidth;
        target.classList.add("taxos-slide-enter");
      }
    }
  }

  async function boot() {
    applyTheme("Light");
    render();
    setTimeout(() => {
      if (state.slideId === "loading") go("welcome", { push: false });
    }, LOADING_MS);

    try {
      state.api = await waitForApi();
      const s = await state.api.get_state();
      state.folder = s.folder || "";
      state.hasGroqKey = Boolean(s.has_groq_key);
      applyTheme("Light");
      await state.api.set_theme("Light");
      render();
    } catch (err) {
      state.error = String(err.message || err);
      render();
    }
  }

  boot();
}
