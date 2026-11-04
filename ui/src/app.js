import iconFolders from "./icons/folders.svg?raw";
import iconTrashSvg from "./icons/trash-2.svg?raw";
import iconLayers from "./icons/layers.svg?raw";
import iconSearch from "./icons/search.svg?raw";
import iconFiles from "./icons/files.svg?raw";
import iconCalendar from "./icons/calendar.svg?raw";
import iconWord from "./icons/whole-word.svg?raw";
import iconFileSearch from "./icons/file-search.svg?raw";
import iconTags from "./icons/tags.svg?raw";
import iconCopy from "./icons/copy.svg?raw";
import iconKanban from "./icons/folder-kanban.svg?raw";
import iconSliders from "./icons/sliders-horizontal.svg?raw";
import iconChevronSvg from "./icons/chevron-down.svg?raw";
import iconFolderSvg from "./icons/folder.svg?raw";

const EXT_COLOR = {
  pdf: "text-red-600",
  doc: "text-blue-600",
  docx: "text-blue-600",
  odt: "text-blue-600",
  txt: "text-stone-600",
  md: "text-stone-600",
  xls: "text-green-600",
  xlsx: "text-green-600",
  csv: "text-green-600",
  ppt: "text-orange-600",
  pptx: "text-orange-600",
  jpg: "text-fuchsia-600",
  jpeg: "text-fuchsia-600",
  png: "text-fuchsia-600",
  gif: "text-fuchsia-600",
  webp: "text-fuchsia-600",
  bmp: "text-fuchsia-600",
  svg: "text-fuchsia-600",
  heic: "text-fuchsia-600",
  mp4: "text-indigo-600",
  mkv: "text-indigo-600",
  avi: "text-indigo-600",
  mov: "text-indigo-600",
  webm: "text-indigo-600",
  wmv: "text-indigo-600",
  mp3: "text-teal-600",
  wav: "text-teal-600",
  flac: "text-teal-600",
  ogg: "text-teal-600",
  m4a: "text-teal-600",
  aac: "text-teal-600",
  zip: "text-amber-600",
  rar: "text-amber-600",
  "7z": "text-amber-600",
  tar: "text-amber-600",
  gz: "text-amber-600",
  tgz: "text-amber-600",
  bz2: "text-amber-600",
  exe: "text-stone-500",
  msi: "text-stone-500",
  deb: "text-stone-500",
  rpm: "text-stone-500",
  appimage: "text-stone-500",
  dmg: "text-stone-500",
  pkg: "text-stone-500",
};

const ORG_METHODS = [
  {
    id: "extension",
    title: "Por extensión",
    description: "Una subcarpeta por cada extensión presente (.pdf, .jpg, .docx, .zip…).",
    enabled: true,
    icon: iconFiles,
  },
  {
    id: "date",
    title: "Por fecha",
    description: "Crea carpetas por año, mes o día según la fecha de modificación.",
    enabled: true,
    icon: iconCalendar,
  },
  {
    id: "name",
    title: "Por nombre",
    description: "Agrupa por palabras del nombre. Si indicas varias, usa la más larga.",
    enabled: true,
    icon: iconWord,
  },
  {
    id: "content",
    title: "Por contenido",
    description: "Abre el archivo y analiza su contenido.",
    enabled: false,
    icon: iconFileSearch,
  },
  {
    id: "tags",
    title: "Por etiquetas",
    description: "No mueve archivos; guarda una etiqueta según el tipo.",
    enabled: true,
    icon: iconTags,
  },
  {
    id: "duplicates",
    title: "Por duplicados",
    description: "Conserva la copia más antigua y mueve el resto a Duplicados.",
    enabled: true,
    icon: iconCopy,
  },
  {
    id: "projects",
    title: "Por proyectos",
    description: "Agrupa los archivos cuyo nombre contiene el nombre del proyecto.",
    enabled: true,
    icon: iconKanban,
  },
  {
    id: "rules",
    title: "Por reglas personalizadas",
    description: "Si ocurre X, haz Y.",
    enabled: false,
    icon: iconSliders,
  },
];

function btn(label, { primary = false, danger = false, muted = false } = {}) {
  const base =
    "inline-flex items-center justify-center rounded-md px-5 py-2.5 taxos-text-body font-medium tracking-wide transition focus:outline-none focus:ring-2 focus:ring-stone-400/40 disabled:cursor-not-allowed disabled:opacity-45";
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

function svgIcon(svg, className = "") {
  const tagged = svg.includes("aria-hidden")
    ? svg
    : svg.replace("<svg", '<svg aria-hidden="true" focusable="false"');
  return `<span class="taxos-icon ${className}">${tagged}</span>`;
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatBatchWhen(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return String(iso);
  return date.toLocaleString("es", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function folderBasename(path) {
  if (!path) return "—";
  const parts = String(path).replace(/\\/g, "/").split("/").filter(Boolean);
  return parts[parts.length - 1] || path;
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
    canUndo: false,
    hasHistory: false,
    historyBatches: [],
    undoTimestamp: null,
    undoPreview: { lines: [], move_count: 0, conflict_count: 0, tags: false },
    tutorialSeen: false,
    previewTipSeen: false,
    undoTipSeen: false,
  };

  async function markFlag(name) {
    const keyMap = {
      tutorial_seen: "tutorialSeen",
      preview_tip_seen: "previewTipSeen",
      undo_tip_seen: "undoTipSeen",
    };
    const stateKey = keyMap[name];
    if (!stateKey || state[stateKey]) return;
    state[stateKey] = true;
    if (!state.api) return;
    try {
      await state.api.set_onboarding_flag(name, true);
    } catch {
      /* la UI ya marcó el tip; se reintentará en otra sesión si falla */
    }
  }

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

  async function withApi(fn) {
    if (!state.api) {
      state.error = "API no lista.";
      render();
      return null;
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

  async function refreshUndo() {
    if (!state.api) return;
    try {
      const status = await state.api.undo_status();
      state.canUndo = Boolean(status?.available);
      state.hasHistory = Boolean(status?.has_history);
      if (Array.isArray(status?.batches)) {
        state.historyBatches = status.batches;
      }
    } catch {
      state.canUndo = false;
      state.hasHistory = false;
    }
  }

  async function refreshHistory() {
    if (!state.api) return;
    try {
      const res = await state.api.history_batches();
      state.historyBatches = res?.batches || [];
      state.hasHistory = Boolean(res?.has_history);
      state.canUndo = Boolean(res?.can_undo);
    } catch {
      state.historyBatches = [];
      state.hasHistory = false;
    }
  }

  function shell(bodyHtml, footerHtml, { bare = false } = {}) {
    if (bare) {
      return `
        <main class="flex min-h-screen flex-1 flex-col">${bodyHtml}</main>
        ${
          state.error
            ? `<p class="px-6 taxos-text-body text-red-700/90">${state.error}</p>`
            : ""
        }
      `;
    }
    return `
      <div class="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-5">
        <main class="flex flex-1 flex-col">${bodyHtml}</main>
        ${
          state.error
            ? `<p class="mt-3 taxos-text-body text-red-700/90">${state.error}</p>`
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

  function heroSlide({ title, imageSrc, imageAlt = "", subtitle, footerHtml, extraHtml = "", step = null }) {
    const stepHtml =
      step != null
        ? `<p class="mt-2 text-xs font-medium uppercase tracking-wider text-stone-400">Paso ${step} de 3</p>`
        : "";
    return `
      <div class="flex min-h-screen w-full flex-col items-center justify-center bg-white px-6 py-8 sm:px-10">
        <div class="flex w-full max-w-2xl flex-col items-center text-center">
          <h2 class="font-display taxos-text-hero font-medium tracking-tight text-stone-900">${title}</h2>
          ${stepHtml}
          <img src="${imageSrc}" alt="${escapeHtml(imageAlt)}" class="taxos-hero-img mt-6 drop-shadow-sm" onerror="this.style.display='none'" />
          <p class="mt-6 max-w-lg taxos-text-body font-light leading-relaxed text-stone-700">${subtitle}</p>
          ${extraHtml}
          ${
            footerHtml
              ? `<footer class="mt-8 flex w-full flex-wrap items-center justify-center gap-2">${footerHtml}</footer>`
              : ""
          }
          ${
            state.error
              ? `<p class="mt-4 taxos-text-body text-red-700/90">${state.error}</p>`
              : ""
          }
        </div>
      </div>
    `;
  }

  function titleBlock(h, p) {
    return `
      <h2 class="font-display taxos-text-title font-medium tracking-tight text-stone-900">${h}</h2>
      <p class="mt-2 taxos-text-body font-light leading-relaxed text-stone-600">${p}</p>
    `;
  }

  function groupIcon(kind, name = "") {
    if (kind === "trash") return svgIcon(iconTrashSvg, "text-stone-500");
    if (kind === "tag") return svgIcon(iconTags, "text-stone-500");
    const key = String(name || "").toLowerCase();
    const color = EXT_COLOR[key] || "text-stone-500";
    return svgIcon(iconFolderSvg, color);
  }

  function historyButton() {
    if (!state.hasHistory) return "";
    return `<button type="button" data-action="open-history" class="${btn("")}">Historial</button>`;
  }

  function renderSlide() {
    const id = state.slideId;

    if (id === "loading") {
      return heroSlide({
        title: "Iniciando Taxos…",
        imageSrc: "./illustrations/filing-system.svg",
        imageAlt: "Ilustración de una persona archivando documentos",
        subtitle: "Preparando el asistente para ordenar tus archivos.",
        extraHtml: `
          <div class="mx-auto mt-8 h-px w-48 overflow-hidden bg-stone-300/80" role="progressbar" aria-valuetext="Cargando">
            <div class="taxos-progress-bar h-full w-1/3 bg-stone-800"></div>
          </div>
        `,
      });
    }

    if (id === "welcome") {
      return `
        <div class="taxos-welcome">
          <button type="button" data-go="objetivo" class="taxos-welcome-skip ${btn("")}">Saltar</button>
          <div class="taxos-welcome-phase taxos-welcome-phase-taxonomy" aria-hidden="true">
            <p class="font-display taxos-text-hero font-medium tracking-tight text-stone-900">
              <strong class="font-semibold">Taxonomía</strong>: ciencia que clasifica y ordena.
            </p>
            <p class="taxos-text-body font-light text-stone-600">De ahí viene Taxos.</p>
          </div>
          <div class="taxos-welcome-phase taxos-welcome-phase-brand">
            <h2 class="font-display taxos-text-hero font-medium tracking-tight text-stone-900">Taxos</h2>
            <div class="mt-8 flex w-full justify-center">
              <button type="button" data-go="objetivo" class="${btn("", { primary: true })}">Comenzar</button>
            </div>
          </div>
          ${
            state.error
              ? `<p class="mt-4 taxos-text-body text-red-700/90">${state.error}</p>`
              : ""
          }
        </div>
      `;
    }

    if (id === "objetivo") {
      return heroSlide({
        title: "Objetivo",
        imageSrc: "./illustrations/goal.svg",
        imageAlt: "Ilustración de una meta",
        subtitle:
          "Nada se mueve ni se borra sin una vista previa y tu confirmación. Taxos ordena una carpeta y puede enviar sobrantes a la papelera (no los elimina para siempre).",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <button type="button" data-go="choose_op" class="${btn("")}">Empezar ahora</button>
          <button type="button" data-go="tut_organize" class="${btn("", { primary: true })}">Ver tutorial</button>
        `,
      });
    }

    if (id === "tut_organize") {
      return heroSlide({
        title: "Organizar",
        step: 1,
        imageSrc: "./illustrations/organizing-projects.svg",
        imageAlt: "Ilustración de archivos agrupados en carpetas",
        subtitle:
          "Agrupa archivos en carpetas según el modo que elijas. Por ejemplo, por extensión: los PDF van a una carpeta PDF.",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <button type="button" data-go="tut_clean" class="${btn("", { primary: true })}">Siguiente</button>
        `,
      });
    }

    if (id === "tut_clean") {
      return heroSlide({
        title: "Eliminar",
        step: 2,
        imageSrc: "./illustrations/inbox-cleanup.svg",
        imageAlt: "Ilustración de una bandeja que se limpia",
        subtitle:
          "Envía a la papelera archivos vacíos, temporales o restos de programas. Puedes recuperarlos desde la papelera del sistema.",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <button type="button" data-go="tut_both" class="${btn("", { primary: true })}">Siguiente</button>
        `,
      });
    }

    if (id === "tut_both") {
      return heroSlide({
        title: "Organizar y eliminar",
        step: 3,
        imageSrc: "./illustrations/completed-tasks.svg",
        imageAlt: "Ilustración de tareas terminadas",
        subtitle:
          "Puedes ordenar y limpiar a la vez. Antes de aplicar, Taxos siempre muestra el plan para que confirmes.",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <button type="button" data-go="choose_op" class="${btn("", { primary: true })}">Elegir operación</button>
        `,
      });
    }

    if (id === "choose_op") {
      const cell =
        "flex min-h-[6.5rem] flex-col items-center justify-center gap-2 rounded-lg border border-stone-300/60 bg-white px-3 py-4 taxos-text-body font-medium tracking-wide text-stone-800 transition hover:border-stone-400 hover:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-400/30";
      const cellMuted =
        "flex min-h-[6.5rem] cursor-not-allowed flex-col items-center justify-center gap-1 rounded-lg border border-stone-200/80 bg-stone-100/50 px-3 py-4 taxos-text-body font-medium tracking-wide text-stone-400";
      const option = (op, label, icon) => `
        <button type="button" data-op="${op}" class="${cell}">
          ${svgIcon(icon, "text-stone-600")}
          <span>${label}</span>
        </button>`;
      return shell(
        `
        ${titleBlock("Elegir operación", "¿Qué quieres hacer en esta pasada?")}
        <div class="mt-8 grid grid-cols-2 gap-3">
          ${option("organize", "Organizar", iconFolders)}
          ${option("clean", "Eliminar", iconTrashSvg)}
          ${option("both", "Ambos", iconLayers)}
          <button type="button" disabled class="${cellMuted}" title="Próximamente">
            ${svgIcon(iconSearch, "text-stone-300")}
            <span>Buscar</span>
            <span class="text-[10px] font-light uppercase tracking-wider">Próximamente</span>
          </button>
        </div>
        `,
        `
        <button type="button" data-go="tut_organize" class="${btn("")}">Cómo funciona</button>
        <div class="ml-auto"></div>
        ${historyButton()}
        `
      );
    }

    if (id === "folder") {
      return shell(
        `
        ${titleBlock("Carpeta", "Elige la carpeta a organizar; por defecto se sugiere la del sistema.")}
        <div class="mt-6 flex items-center gap-3 border-b border-stone-300/70 py-3">
          <p class="min-w-0 flex-1 break-all taxos-text-body font-light text-stone-700">${state.folder || "—"}</p>
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
        "flex min-h-[7.5rem] flex-col items-start justify-center rounded-lg border border-stone-300/70 bg-white px-4 py-4 text-left transition hover:border-stone-500 hover:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-400/30";
      const cellOff =
        "flex min-h-[7.5rem] cursor-not-allowed flex-col items-start justify-center rounded-lg border border-stone-200/80 bg-stone-50/80 px-4 py-4 text-left opacity-70";
      const cards = ORG_METHODS.map((m) => {
        if (m.enabled) {
          return `
            <button type="button" data-org-method="${m.id}" class="${cellOn}">
              <span class="flex items-center gap-2">
                ${svgIcon(m.icon, "text-stone-700")}
                <span class="font-display text-lg font-medium text-stone-900">${m.title}</span>
              </span>
              <span class="mt-2 text-xs font-light leading-relaxed text-stone-500">${m.description}</span>
            </button>`;
        }
        return `
          <button type="button" disabled class="${cellOff}" title="Próximamente">
            <span class="flex items-center gap-2">
              ${svgIcon(m.icon, "text-stone-400")}
              <span class="font-display text-lg font-medium text-stone-400">${m.title}</span>
            </span>
            <span class="mt-2 text-xs font-light leading-relaxed text-stone-400">${m.description}</span>
            <span class="mt-2 text-[10px] font-medium uppercase tracking-wider text-stone-400">Próximamente</span>
          </button>`;
      }).join("");

      return shell(
        `
        ${titleBlock("Forma de organizar", "Elige cómo clasificar los archivos. Luego verás la vista previa por carpetas.")}
        <div class="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">${cards}</div>
        `,
        `<button type="button" data-action="back" class="${btn("")}">Atrás</button>`
      );
    }

    if (id === "org_config") {
      if (state.orgMethod === "date") {
        const choice =
          "flex min-h-[5.5rem] flex-col items-center justify-center rounded-lg border border-stone-300/70 bg-white px-4 py-4 taxos-text-body font-medium text-stone-800 transition hover:border-stone-500 hover:bg-stone-50";
        return shell(
          `
          ${titleBlock("Por fecha", "Las carpetas usan la fecha de modificación del archivo.")}
          <div class="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <button type="button" data-granularity="year" class="${choice}">Por año</button>
            <button type="button" data-granularity="month" class="${choice}">Por mes</button>
            <button type="button" data-granularity="day" class="${choice}">Por día</button>
          </div>
          `,
          `<button type="button" data-action="back" class="${btn("")}">Atrás</button>`
        );
      }

      const projects = state.orgMethod === "projects";
      return shell(
        `
        ${titleBlock(
          projects ? "Nombres de proyecto" : "Palabras del nombre",
          projects
            ? "Escribe uno o más nombres separados por comas. Si el nombre del archivo contiene esa palabra, sin distinguir mayúsculas, va a una carpeta con ese nombre. Si coinciden varias, se usa la más larga."
            : "Opcional. Si escribes palabras, cada archivo va a la carpeta de la coincidencia más larga. Si lo dejas vacío, se usa la primera palabra del nombre."
        )}
        <label class="mt-8 block text-xs font-medium uppercase tracking-wider text-stone-500" for="org-terms">
          ${projects ? "Proyectos" : "Palabras"}
        </label>
        <input id="org-terms" type="text" autocomplete="off"
          placeholder="${projects ? "Taxos, Informe" : "factura, contrato"}"
          class="mt-2 w-full border-0 border-b border-stone-300 bg-transparent py-3 taxos-text-body font-light text-stone-800 outline-none focus:border-stone-800" />
        `,
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="org-config-next" class="${btn("", { primary: true })}">Ver vista previa</button>
        `
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
                const detail =
                  g.kind === "tag"
                    ? `${g.count} archivo${g.count === 1 ? "" : "s"} · etiqueta · ${escapeHtml(g.size_label || "")}`
                    : `${g.count} archivo${g.count === 1 ? "" : "s"} · ${escapeHtml(g.size_label || "")}`;
                return `
              <li>
                <button type="button" data-expand="${escapeHtml(g.name)}"
                  class="flex w-full items-center gap-3 py-3.5 text-left transition hover:bg-stone-50/80 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-stone-300/50">
                  ${groupIcon(g.kind, g.name)}
                  <div class="min-w-0 flex-1">
                    <p class="truncate taxos-text-body font-medium text-stone-900">${escapeHtml(g.name)}</p>
                    <p class="mt-0.5 text-xs font-light text-stone-500">${detail}</p>
                  </div>
                  ${svgIcon(iconChevronSvg, `text-stone-400 transition ${open ? "rotate-180" : ""}`)}
                </button>
                ${filesHtml}
              </li>`;
              })
              .join("")}
          </ul>`
        : `<p class="mt-8 taxos-text-body font-light text-stone-500">Nada que hacer en esta carpeta con la operación elegida.</p>`;

      const previewTip = state.previewTipSeen
        ? ""
        : `
        <div class="taxos-callout mt-6" role="status">
          <p class="taxos-text-body font-light text-stone-700">
            Esto es solo un plan: aún no se ha movido ni borrado nada. Nada cambia hasta que confirmes.
          </p>
          <button type="button" data-action="dismiss-preview-tip" class="mt-2 text-xs font-medium text-stone-500 underline-offset-2 hover:underline">
            Entendido
          </button>
        </div>`;

      return shell(
        `
        ${titleBlock("Vista previa", "Resumen por carpeta antes de aplicar. Pulsa una carpeta para ver los archivos.")}
        ${previewTip}
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
      const tagged = state.preview.tagCount || 0;
      const extra = tagged ? ` Se etiquetarán ${tagged} archivo(s), sin moverlos.` : "";
      return shell(
        titleBlock(
          "Confirmación",
          `Se van a mover ${state.preview.moveCount} archivo(s) y enviar ${state.preview.trashCount} a la papelera.${extra} ¿Confirmas aplicar el plan?`
        ),
        `
        <button type="button" data-action="confirm-no" class="${btn("")}">No</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="apply" class="${btn("", { primary: true })}" ${state.busy ? "disabled" : ""}>Sí, aplicar</button>
        `
      );
    }

    if (id === "history") {
      const batches = state.historyBatches || [];
      const list = batches.length
        ? `<ul class="mt-6 divide-y divide-stone-300/50 border-y border-stone-300/50">
            ${batches
              .map((batch) => {
                const kindLabel = batch.kind === "clean" ? "Limpiar" : "Organizar";
                const canUndo = Boolean(batch.can_undo);
                const status = canUndo
                  ? "Se puede deshacer"
                  : batch.kind === "clean"
                    ? "No deshacible desde Taxos"
                    : "Ya deshecho o no disponible";
                return `
              <li>
                <button type="button"
                  data-history-ts="${escapeHtml(batch.timestamp || "")}"
                  data-history-kind="${escapeHtml(batch.kind || "")}"
                  data-history-can-undo="${canUndo ? "1" : "0"}"
                  class="flex w-full flex-col gap-1 py-3.5 text-left transition hover:bg-stone-50/80 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-stone-300/50">
                  <div class="flex items-center justify-between gap-3">
                    <p class="taxos-text-body font-medium text-stone-900">${kindLabel}</p>
                    <p class="shrink-0 text-xs font-light text-stone-500">${escapeHtml(formatBatchWhen(batch.timestamp))}</p>
                  </div>
                  <p class="text-xs font-light text-stone-600">
                    ${escapeHtml(folderBasename(batch.root))} · ${batch.file_count || 0} archivo${(batch.file_count || 0) === 1 ? "" : "s"}
                  </p>
                  <p class="text-xs font-light ${canUndo ? "text-stone-500" : "text-stone-400"}">${status}</p>
                </button>
              </li>`;
              })
              .join("")}
          </ul>`
        : `<p class="mt-8 taxos-text-body font-light text-stone-500">Aún no hay operaciones en el historial.</p>`;

      return shell(
        `
        ${titleBlock("Historial", "Organizaciones y limpiezas registradas. Solo se puede deshacer una organización.")}
        ${list}
        `,
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        `
      );
    }

    if (id === "undo_confirm") {
      const preview = state.undoPreview || {};
      const lines = preview.lines || [];
      const list = lines.length
        ? `<ul class="mt-6 max-h-48 space-y-1 overflow-y-auto border-y border-stone-300/50 py-3 taxos-text-body font-light text-stone-600">
            ${lines.map((line) => `<li class="truncate">${escapeHtml(line)}</li>`).join("")}
          </ul>`
        : "";
      const conflicts = preview.conflict_count || 0;
      const conflict = conflicts
        ? `<p class="mt-3 taxos-text-body font-light text-stone-600">Hay ${conflicts} ${
            conflicts === 1
              ? "archivo cuya ruta original está ocupada: se restaura con otro nombre."
              : "archivos cuya ruta original está ocupada: se restauran con otro nombre."
          }</p>`
        : "";
      return shell(
        `
        ${titleBlock(
          "Deshacer",
          "Cada archivo vuelve a su ruta original. Las carpetas que creó Taxos y queden vacías se eliminan."
        )}
        ${conflict}
        ${list}
        `,
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="undo-apply" class="${btn("", { primary: true })}" ${state.busy ? "disabled" : ""}>Deshacer</button>
        `
      );
    }

    if (id === "done") {
      const undoTip =
        !state.undoTipSeen && state.hasHistory
          ? `<p class="taxos-callout mt-6 taxos-text-body font-light text-stone-700" role="status">
              Puedes deshacer organizaciones desde Historial.
            </p>`
          : "";
      return shell(
        `
        ${titleBlock("Listo", state.resultMessage)}
        ${undoTip}
        `,
        `
        <button type="button" data-action="close" class="${btn("")}">Cerrar</button>
        <div class="ml-auto flex flex-wrap gap-2">
          ${historyButton()}
          <button type="button" data-action="again" class="${btn("", { primary: true })}">Realizar otra operación</button>
        </div>
        `
      );
    }

    return shell(`<p class="taxos-text-body text-stone-600">Slide desconocido.</p>`, "");
  }

  function bind() {
    root.querySelectorAll("[data-go]").forEach((el) => {
      el.addEventListener("click", async () => {
        const dest = el.getAttribute("data-go");
        if (dest === "choose_op") {
          await markFlag("tutorial_seen");
          await refreshUndo();
        }
        if (dest === "confirm") {
          await markFlag("preview_tip_seen");
        }
        go(dest);
      });
    });

    root.querySelector('[data-action="back"]')?.addEventListener("click", back);

    root.querySelector('[data-action="dismiss-preview-tip"]')?.addEventListener("click", async () => {
      await markFlag("preview_tip_seen");
      render({ animate: false });
    });

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
        if (method === "date" || method === "name" || method === "projects") {
          go("org_config");
          return;
        }
        await prepareAndPreview(method, "month", "");
      });
    });

    root.querySelectorAll("[data-granularity]").forEach((el) => {
      el.addEventListener("click", async () => {
        await prepareAndPreview("date", el.getAttribute("data-granularity") || "month", "");
      });
    });

    root.querySelector('[data-action="org-config-next"]')?.addEventListener("click", async () => {
      const terms = root.querySelector("#org-terms")?.value || "";
      await prepareAndPreview(state.orgMethod, "month", terms);
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
        const ready = await loadPreview();
        if (ready) go("preview");
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
      state.canUndo = Boolean(res.can_undo);
      state.hasHistory = Boolean(res.has_history ?? true);
      go("done");
    });

    root.querySelector('[data-action="open-history"]')?.addEventListener("click", async () => {
      await markFlag("undo_tip_seen");
      await refreshHistory();
      go("history");
    });

    root.querySelectorAll("[data-history-ts]").forEach((el) => {
      el.addEventListener("click", async () => {
        const ts = el.getAttribute("data-history-ts") || "";
        const kind = el.getAttribute("data-history-kind") || "";
        const canUndo = el.getAttribute("data-history-can-undo") === "1";
        if (kind === "clean" || !canUndo) {
          state.error =
            kind === "clean"
              ? "La papelera no se restaura desde Taxos. Recupera los archivos desde la papelera del sistema."
              : "Este lote ya no se puede deshacer.";
          render({ animate: false });
          return;
        }
        await openUndo(ts);
      });
    });

    root.querySelector('[data-action="undo-apply"]')?.addEventListener("click", async () => {
      const ts = state.undoTimestamp;
      const res = await withApi((api) => api.apply_undo(ts || null));
      if (!res || res.ok === false) {
        state.error = (res && res.error) || "No se pudo deshacer.";
        render({ animate: false });
        return;
      }
      state.resultMessage = res.message || "Organización deshecha.";
      state.canUndo = Boolean(res.can_undo);
      state.hasHistory = Boolean(res.has_history);
      state.undoTimestamp = null;
      go("done");
    });

    root.querySelector('[data-action="close"]')?.addEventListener("click", async () => {
      await markFlag("undo_tip_seen");
      await withApi((api) => api.close_app());
    });

    root.querySelector('[data-action="again"]')?.addEventListener("click", async () => {
      await markFlag("undo_tip_seen");
      await withApi((api) => api.reset_operation());
      state.useAi = false;
      state.orgMethod = null;
      state.preview = { moveCount: 0, trashCount: 0, tagCount: 0, groups: [], lines: [] };
      state.expandedGroup = null;
      state.history = [];
      state.undoTimestamp = null;
      await refreshUndo();
      go("choose_op", { push: false });
    });
  }

  async function prepareAndPreview(method, granularity, terms) {
    const res = await withApi((api) => api.set_organize_options(method, granularity, terms));
    if (!res || res.ok === false) {
      state.error = (res && res.error) || "No se pudo preparar el modo.";
      render({ animate: false });
      return;
    }
    state.useAi = false;
    await withApi((api) => api.set_use_ai(false));
    const ready = await loadPreview();
    if (ready) go("preview");
  }

  async function openUndo(timestamp) {
    const res = await withApi((api) => api.undo_preview(timestamp || null));
    if (!res || res.available === false) {
      state.error = "No hay una organización para deshacer.";
      state.canUndo = false;
      render({ animate: false });
      return;
    }
    state.undoPreview = res;
    state.undoTimestamp = res.timestamp || timestamp || null;
    state.canUndo = true;
    go("undo_confirm");
  }

  async function loadPreview() {
    const res = await withApi((api) => api.build_preview());
    if (!res) return false;
    if (res.error) {
      state.error = res.error;
      render({ animate: false });
      return false;
    }
    state.preview = {
      moveCount: res.move_count ?? 0,
      trashCount: res.trash_count ?? 0,
      tagCount: res.tag_count ?? 0,
      groups: res.groups || [],
      lines: res.lines || [],
    };
    state.expandedGroup = null;
    return true;
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

    try {
      state.api = await waitForApi();
      const s = await state.api.get_state();
      state.folder = s.folder || "";
      state.hasGroqKey = Boolean(s.has_groq_key);
      state.tutorialSeen = Boolean(s.tutorial_seen);
      state.previewTipSeen = Boolean(s.preview_tip_seen);
      state.undoTipSeen = Boolean(s.undo_tip_seen);
      applyTheme("Light");
      await state.api.set_theme("Light");
      await refreshUndo();
      if (state.tutorialSeen) {
        go("choose_op", { push: false });
      } else {
        go("welcome", { push: false });
      }
    } catch (err) {
      state.error = String(err.message || err);
      render();
    }
  }

  boot();
}
