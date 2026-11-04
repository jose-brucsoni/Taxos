import iconFolders from "./icons/folders.svg?raw";
import iconTrashSvg from "./icons/trash-2.svg?raw";
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
    busyMessage: "",
    busyLock: false,
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
    doSearch: false,
    cleanItems: [],
    cleanSortBy: "name",
    cleanSortReverse: false,
    searchScope: "folder",
    searchMode: "name",
    searchName: "",
    searchExt: "",
    searchHits: [],
    searchRoot: "",
    searchTruncated: false,
    cleanRoots: [],
    cleanTotalLabel: "",
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

  async function withApi(fn, { message } = {}) {
    if (!state.api) {
      state.error = "API no lista.";
      render();
      return null;
    }
    const outer = !state.busyLock;
    if (outer) {
      state.busy = true;
      state.busyMessage = message || "Trabajando…";
      state.error = "";
      render({ animate: false });
    } else if (message) {
      state.busyMessage = message;
      render({ animate: false });
    }
    try {
      return await fn(state.api);
    } catch (err) {
      state.error = String(err?.message || err);
      render({ animate: false });
      return null;
    } finally {
      if (outer) {
        state.busy = false;
        state.busyMessage = "";
        render({ animate: false });
      }
    }
  }

  async function runBusy(message, asyncFn) {
    state.busy = true;
    state.busyMessage = message || "Trabajando…";
    state.busyLock = true;
    state.error = "";
    render({ animate: false });
    try {
      return await asyncFn();
    } finally {
      state.busyLock = false;
      state.busy = false;
      state.busyMessage = "";
      render({ animate: false });
    }
  }

  function busyOverlayHtml() {
    if (!state.busy) return "";
    const msg = escapeHtml(state.busyMessage || "Trabajando…");
    return `
      <div class="taxos-busy-overlay" role="status" aria-live="polite" aria-busy="true">
        <div class="taxos-busy-panel">
          <p class="font-display taxos-text-title font-medium tracking-tight text-stone-900">${msg}</p>
          <div class="mx-auto mt-8 h-px w-48 overflow-hidden bg-stone-300/80" role="progressbar" aria-valuetext="${msg}">
            <div class="taxos-progress-bar h-full w-1/3 bg-stone-800"></div>
          </div>
        </div>
      </div>`;
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

  function heroSlide({ title, imageSrc, imageAlt = "", subtitle, footerHtml, extraHtml = "", step = null, stepTotal = 2 }) {
    const stepHtml =
      step != null
        ? `<p class="mt-2 text-xs font-medium uppercase tracking-wider text-stone-400">Paso ${step} de ${stepTotal}</p>`
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
          "Nada se mueve ni se borra sin vista previa y tu confirmación. Puedes organizar una carpeta, limpiar temps/caché del usuario o buscar archivos.",
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
          "Escanea temps y caché de tu usuario, propone basura típica de tu sistema y tú marcas qué enviar a la papelera. Nada se borra sin confirmar.",
        footerHtml: `
          <button type="button" data-action="back" class="${btn("")}">Atrás</button>
          <button type="button" data-go="choose_op" class="${btn("", { primary: true })}">Elegir operación</button>
        `,
      });
    }

    if (id === "choose_op") {
      const cell =
        "flex w-full min-h-[5.5rem] flex-col items-center justify-center gap-2 rounded-lg border border-stone-300/60 bg-white px-4 py-5 taxos-text-body font-medium tracking-wide text-stone-800 transition hover:border-stone-400 hover:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-400/30";
      const option = (op, label, icon) => `
        <button type="button" data-op="${op}" class="${cell}">
          ${svgIcon(icon, "text-stone-600")}
          <span>${label}</span>
        </button>`;
      return shell(
        `
        <div class="flex flex-1 flex-col items-center justify-center py-6">
          ${titleBlock("Elegir operación", "¿Qué quieres hacer?")}
          <div class="mt-10 flex w-full max-w-sm flex-col gap-3">
            ${option("organize", "Organizar", iconFolders)}
            ${option("clean", "Eliminar", iconTrashSvg)}
            ${option("search", "Buscar", iconSearch)}
          </div>
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
        <button type="button" data-action="preview-next" class="${btn("", { primary: true })}" ${state.busy ? "disabled" : ""}>Continuar</button>
        `
      );
    }

    if (id === "clean_select") {
      const selectedCount = state.cleanItems.filter((i) => i.selected).length;
      const sortOpts = [
        ["name", "Nombre"],
        ["size", "Tamaño"],
        ["extension", "Extensión"],
        ["reason", "Motivo"],
      ]
        .map(
          ([value, label]) =>
            `<option value="${value}" ${state.cleanSortBy === value ? "selected" : ""}>${label}</option>`
        )
        .join("");
      const rows = state.cleanItems.length
        ? state.cleanItems
            .map(
              (item) => `
            <label class="taxos-clean-row flex items-start gap-3 border-b border-stone-200/80 py-3">
              <input type="checkbox" data-clean-path="${escapeHtml(item.path)}" class="mt-1" ${item.selected ? "checked" : ""} />
              <span class="min-w-0 flex-1">
                <span class="block taxos-text-body font-medium text-stone-900 truncate">${escapeHtml(item.name)}</span>
                <span class="block text-xs font-light text-stone-500 truncate">${escapeHtml(item.rel_path)}</span>
                <span class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs font-light text-stone-600">
                  <span>.${escapeHtml(item.extension || "—")}</span>
                  <span>${escapeHtml(item.size_label)}</span>
                  <span>${escapeHtml(item.reason)}</span>
                </span>
              </span>
            </label>`
            )
            .join("")
        : `<p class="mt-6 taxos-text-body font-light text-stone-500">No se encontró basura conocida en temps/caché.</p>`;
      const rootsLabel = (state.cleanRoots || []).length
        ? state.cleanRoots.map((r) => escapeHtml(r)).join(" · ")
        : "temps y caché del usuario";

      return shell(
        `
        ${titleBlock("Eliminar", "Marca qué enviar a la papelera. Puedes ordenar la lista.")}
        <div class="mt-4 flex flex-wrap items-center gap-2">
          <label class="text-xs font-medium uppercase tracking-wider text-stone-500">
            Ordenar
            <select data-clean-sort class="ml-2 rounded border border-stone-300 bg-white px-2 py-1 text-sm font-normal normal-case tracking-normal text-stone-800">
              ${sortOpts}
            </select>
          </label>
          <button type="button" data-action="clean-sort-dir" class="${btn("")}">${state.cleanSortReverse ? "Desc" : "Asc"}</button>
          <button type="button" data-action="clean-select-all" class="${btn("")}">Todos</button>
          <button type="button" data-action="clean-select-none" class="${btn("")}">Ninguno</button>
          <span class="ml-auto text-xs font-light text-stone-500">${selectedCount} / ${state.cleanItems.length}${state.cleanTotalLabel ? ` · ${escapeHtml(state.cleanTotalLabel)}` : ""}</span>
        </div>
        <div class="mt-2 max-h-[40vh] overflow-y-auto border-y border-stone-300/50">${rows}</div>
        <aside class="taxos-clean-explain mt-6" role="note">
          <p><strong>Por qué:</strong> coinciden con basura típica de este sistema (temporales, vacíos, locks…).</p>
          <p><strong>Objetivo:</strong> liberar espacio y reducir ruido en cachés y carpetas temporales del usuario.</p>
          <p><strong>Lugar:</strong> ${rootsLabel}</p>
          <p><strong>Qué mejora:</strong> menos archivos basura; no se tocan programas del sistema; todo va a la papelera (recuperable).</p>
        </aside>
        `,
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="clean-next" class="${btn("", { primary: true })}" ${selectedCount < 1 && state.cleanItems.length ? "disabled" : ""} ${state.busy ? "disabled" : ""}>
          ${state.cleanItems.length ? "Continuar" : "Volver"}
        </button>
        `
      );
    }

    if (id === "search_scope") {
      const cell =
        "flex min-h-[5.5rem] flex-col items-center justify-center gap-2 rounded-lg border border-stone-300/60 bg-white px-3 py-4 taxos-text-body font-medium tracking-wide text-stone-800 transition hover:border-stone-400 hover:bg-stone-50";
      return shell(
        `
        ${titleBlock("Buscar", "¿Dónde quieres buscar? Solo archivos de tu usuario, no del sistema.")}
        <div class="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <button type="button" data-action="search-scope-folder" class="${cell}">Carpeta concreta</button>
          <button type="button" data-action="search-scope-all" class="${cell}">Buscar en toda la PC</button>
        </div>
        `,
        `<button type="button" data-action="back" class="${btn("")}">Atrás</button>`
      );
    }

    if (id === "search_query") {
      const modeBtn = (mode, label) => {
        const active = state.searchMode === mode;
        return `<button type="button" data-search-mode="${mode}" class="${btn("", { primary: active })}">${label}</button>`;
      };
      const field =
        state.searchMode === "extension"
          ? `<label class="block">
              <span class="text-xs font-medium uppercase tracking-wider text-stone-500">Extensión</span>
              <input type="text" id="search-ext" value="${escapeHtml(state.searchExt)}" class="mt-1 w-full border-b border-stone-300 bg-transparent py-2 taxos-text-body text-stone-800 outline-none focus:border-stone-600" placeholder="p. ej. pdf" />
            </label>`
          : `<label class="block">
              <span class="text-xs font-medium uppercase tracking-wider text-stone-500">Nombre contiene</span>
              <input type="text" id="search-name" value="${escapeHtml(state.searchName)}" class="mt-1 w-full border-b border-stone-300 bg-transparent py-2 taxos-text-body text-stone-800 outline-none focus:border-stone-600" placeholder="p. ej. factura" />
            </label>`;
      return shell(
        `
        ${titleBlock("Criterios", "Elige cómo buscar. No se lee el contenido de los archivos.")}
        <div class="mt-6 flex flex-wrap gap-2">
          ${modeBtn("name", "Por nombre")}
          ${modeBtn("extension", "Por extensión")}
        </div>
        <div class="mt-6 space-y-4">
          ${field}
          ${
            state.searchScope === "all_user"
              ? `<p class="text-xs font-light text-stone-500">Ámbito: perfil de usuario (toda la PC de usuario).</p>`
              : `<p class="text-xs font-light text-stone-500 break-all">Ámbito: ${escapeHtml(state.folder || "—")}</p>`
          }
        </div>
        `,
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="search-run" class="${btn("", { primary: true })}" ${state.busy ? "disabled" : ""}>Buscar</button>
        `
      );
    }

    if (id === "search_results") {
      const list = state.searchHits.length
        ? `<ul class="mt-6 max-h-[50vh] divide-y divide-stone-200/80 overflow-y-auto border-y border-stone-300/50">
            ${state.searchHits
              .map(
                (hit) => `
              <li class="flex items-start justify-between gap-3 py-3">
                <div class="min-w-0">
                  <p class="taxos-text-body font-medium text-stone-900 truncate">${escapeHtml(hit.name)}</p>
                  <p class="text-xs font-light text-stone-500 break-all">${escapeHtml(hit.parent)}</p>
                  <p class="mt-1 text-xs font-light text-stone-600">${escapeHtml(hit.size_label)} · .${escapeHtml(hit.extension || "—")}</p>
                </div>
                <button type="button" data-reveal="${escapeHtml(hit.path)}" class="${btn("")}">Ver ubicación</button>
              </li>`
              )
              .join("")}
          </ul>`
        : `<p class="mt-8 taxos-text-body font-light text-stone-500">Sin coincidencias.</p>`;
      const note = state.searchTruncated
        ? `<p class="mt-2 text-xs font-light text-stone-500">Se alcanzó el límite de resultados.</p>`
        : "";
      return shell(
        `
        ${titleBlock("Resultados", `${state.searchHits.length} archivo(s) en ${state.searchRoot || "—"}.`)}
        ${note}
        ${list}
        `,
        `
        <button type="button" data-action="back" class="${btn("")}">Atrás</button>
        <div class="ml-auto"></div>
        <button type="button" data-action="again" class="${btn("", { primary: true })}">Otra operación</button>
        `
      );
    }

    if (id === "confirm") {
      const tagged = state.preview.tagCount || 0;
      const trashCount = state.doClean
        ? state.cleanItems.filter((i) => i.selected).length
        : 0;
      let summary;
      if (state.doClean && !state.doOrganize) {
        summary = `Se enviarán ${trashCount} archivo(s) a la papelera. ¿Confirmas?`;
      } else {
        const extra = tagged ? ` Se etiquetarán ${tagged} archivo(s), sin moverlos.` : "";
        summary = `Se van a mover ${state.preview.moveCount} archivo(s).${extra} ¿Confirmas aplicar el plan?`;
      }
      return shell(
        titleBlock("Confirmación", summary),
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
      if (state.doClean) {
        go("clean_select", { push: false });
      } else {
        go("preview", { push: false });
      }
    });

    root.querySelector('[data-action="preview-next"]')?.addEventListener("click", () => {
      go("confirm");
    });

    root.querySelector("[data-clean-sort]")?.addEventListener("change", async (ev) => {
      state.cleanSortBy = ev.target.value || "name";
      await loadCleanPreview({ updating: true });
      render({ animate: false });
    });

    root.querySelector('[data-action="clean-sort-dir"]')?.addEventListener("click", async () => {
      state.cleanSortReverse = !state.cleanSortReverse;
      await loadCleanPreview({ updating: true });
      render({ animate: false });
    });

    root.querySelectorAll("[data-clean-path]").forEach((el) => {
      el.addEventListener("change", () => {
        const path = el.getAttribute("data-clean-path");
        const item = state.cleanItems.find((i) => i.path === path);
        if (item) item.selected = Boolean(el.checked);
        render({ animate: false });
      });
    });

    root.querySelector('[data-action="clean-select-all"]')?.addEventListener("click", () => {
      state.cleanItems.forEach((i) => {
        i.selected = true;
      });
      render({ animate: false });
    });

    root.querySelector('[data-action="clean-select-none"]')?.addEventListener("click", () => {
      state.cleanItems.forEach((i) => {
        i.selected = false;
      });
      render({ animate: false });
    });

    root.querySelector('[data-action="clean-next"]')?.addEventListener("click", async () => {
      const selected = state.cleanItems.filter((i) => i.selected).map((i) => i.path);
      if (!state.cleanItems.length) {
        go("choose_op", { push: false });
        return;
      }
      if (selected.length === 0) {
        state.error = "Marca al menos un archivo o pulsa Atrás.";
        render({ animate: false });
        return;
      }
      await withApi((api) => api.set_clean_selection(selected));
      state.preview.trashCount = selected.length;
      go("confirm");
    });

    root.querySelectorAll("[data-search-mode]").forEach((el) => {
      el.addEventListener("click", () => {
        state.searchMode = el.getAttribute("data-search-mode") || "name";
        render({ animate: false });
      });
    });

    root.querySelector('[data-action="search-scope-folder"]')?.addEventListener("click", () => {
      state.searchScope = "folder";
      go("folder");
    });

    root.querySelector('[data-action="search-scope-all"]')?.addEventListener("click", () => {
      state.searchScope = "all_user";
      go("search_query");
    });

    root.querySelector('[data-action="search-run"]')?.addEventListener("click", async () => {
      if (state.searchMode === "extension") {
        state.searchExt = root.querySelector("#search-ext")?.value || "";
        state.searchName = "";
        if (!state.searchExt.trim()) {
          state.error = "Indica una extensión.";
          render({ animate: false });
          return;
        }
      } else {
        state.searchName = root.querySelector("#search-name")?.value || "";
        state.searchExt = "";
        if (!state.searchName.trim()) {
          state.error = "Indica un texto para el nombre.";
          render({ animate: false });
          return;
        }
      }
      const res = await withApi(
        (api) => api.search_files(state.searchName, state.searchExt, state.searchScope, 500),
        { message: "Buscando archivos…" }
      );
      if (!res) return;
      if (res.ok === false) {
        state.error = res.error || "No se pudo buscar.";
        render({ animate: false });
        return;
      }
      state.searchHits = res.hits || [];
      state.searchRoot = res.root || "";
      state.searchTruncated = Boolean(res.truncated);
      go("search_results");
    });

    root.querySelectorAll("[data-reveal]").forEach((el) => {
      el.addEventListener("click", async () => {
        const path = el.getAttribute("data-reveal");
        await withApi((api) => api.reveal_path(path));
      });
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
        if (kind === "clean") {
          const ready = await runBusy("Escaneando basura…", async () => {
            await withApi((api) => api.set_operation(kind));
            state.doSearch = false;
            state.doOrganize = false;
            state.doClean = true;
            state.orgMethod = null;
            state.cleanItems = [];
            return loadCleanPreview({ nested: true });
          });
          if (ready) go("clean_select");
          else render({ animate: false });
          return;
        }
        await withApi((api) => api.set_operation(kind));
        state.doSearch = kind === "search";
        state.doOrganize = kind === "organize";
        state.doClean = false;
        state.orgMethod = null;
        state.cleanItems = [];
        if (kind === "search") {
          go("search_scope");
          return;
        }
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
      if (state.doSearch) {
        state.searchScope = "folder";
        go("search_query");
        return;
      }
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
      const res = await runBusy("Aplicando cambios…", async () => {
        if (state.doClean) {
          const selected = state.cleanItems.filter((i) => i.selected).map((i) => i.path);
          await withApi((api) => api.set_clean_selection(selected));
        }
        return withApi((api) => api.apply_plan());
      });
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
      const res = await withApi((api) => api.apply_undo(ts || null), { message: "Deshaciendo…" });
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
      state.doSearch = false;
      state.preview = { moveCount: 0, trashCount: 0, tagCount: 0, groups: [], lines: [] };
      state.cleanItems = [];
      state.searchHits = [];
      state.expandedGroup = null;
      state.history = [];
      state.undoTimestamp = null;
      await refreshUndo();
      go("choose_op", { push: false });
    });
  }

  async function prepareAndPreview(method, granularity, terms) {
    const ready = await runBusy("Preparando vista previa…", async () => {
      const res = await withApi((api) => api.set_organize_options(method, granularity, terms));
      if (!res || res.ok === false) {
        state.error = (res && res.error) || "No se pudo preparar el modo.";
        return false;
      }
      state.useAi = false;
      await withApi((api) => api.set_use_ai(false));
      return loadPreview({ nested: true });
    });
    if (ready) go("preview");
    else render({ animate: false });
  }

  async function openUndo(timestamp) {
    const res = await withApi((api) => api.undo_preview(timestamp || null), {
      message: "Preparando deshacer…",
    });
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

  async function loadPreview({ nested = false } = {}) {
    const res = nested
      ? await withApi((api) => api.build_preview())
      : await withApi((api) => api.build_preview(), { message: "Preparando vista previa…" });
    if (!res) return false;
    if (res.error) {
      state.error = res.error;
      if (!nested) render({ animate: false });
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

  async function loadCleanPreview({ updating = false, nested = false } = {}) {
    const res = nested
      ? await withApi((api) => api.build_clean_preview(state.cleanSortBy, state.cleanSortReverse))
      : await withApi(
          (api) => api.build_clean_preview(state.cleanSortBy, state.cleanSortReverse),
          { message: updating ? "Actualizando lista…" : "Escaneando basura…" }
        );
    if (!res) return false;
    if (res.ok === false) {
      state.error = res.error || "No se pudo escanear basura.";
      render({ animate: false });
      return false;
    }
    const previous = new Map(state.cleanItems.map((i) => [i.path, i.selected]));
    state.cleanItems = (res.items || []).map((item) => ({
      ...item,
      selected: previous.has(item.path) ? previous.get(item.path) : item.selected !== false,
    }));
    state.cleanRoots = res.roots || [];
    state.cleanTotalLabel = res.total_size_label || "";
    return true;
  }

  function render({ animate = false } = {}) {
    root.innerHTML = `${renderSlide()}${busyOverlayHtml()}`;
    if (!state.busy) {
      bind();
    }
    if (animate && !state.busy) {
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
