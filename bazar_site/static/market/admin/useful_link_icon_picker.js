(() => {
  const INPUT_NAME = "icon_class";
  const JSON_URLS = [
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.json",
    "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.11.3/font/bootstrap-icons.json",
  ];
  const ICONS_CSS_URLS = [
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.11.3/font/bootstrap-icons.min.css",
  ];

  function el(tag, attrs = {}, children = []) {
    const n = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
      if (k === "class") n.className = v;
      else if (k === "html") n.innerHTML = v;
      else n.setAttribute(k, v);
    });
    children.forEach((c) => n.appendChild(c));
    return n;
  }

  function getIconNameFromInput(value) {
    const v = (value || "").trim();
    if (!v) return "";
    // accept "bi bi-xxx" or "bi-xxx" or "xxx"
    const parts = v.split(/\s+/).filter(Boolean);
    const biClass = parts.find((p) => p.startsWith("bi-")) || parts[0];
    return biClass.replace(/^bi-/, "");
  }

  function setInputToIcon(input, iconName) {
    input.value = iconName ? `bi bi-${iconName}` : "";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  async function fetchIconsJson() {
    let lastErr = null;
    for (const url of JSON_URLS) {
      try {
        const res = await fetch(url, { cache: "force-cache" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
      } catch (e) {
        lastErr = e;
      }
    }
    throw lastErr || new Error("Failed to fetch icons JSON");
  }

  function ensureBootstrapIconsCss() {
    if (document.getElementById("useful-link-bootstrap-icons-css")) return;

    // If already present (some other part of site/admin), don't add a duplicate.
    const already = Array.from(document.querySelectorAll("link[rel='stylesheet']")).some((l) =>
      (l.getAttribute("href") || "").includes("bootstrap-icons")
    );
    if (already) return;

    const link = el("link", {
      id: "useful-link-bootstrap-icons-css",
      rel: "stylesheet",
      href: ICONS_CSS_URLS[0],
      crossorigin: "anonymous",
    });

    link.addEventListener("error", () => {
      // Fallback if primary CDN fails
      link.setAttribute("href", ICONS_CSS_URLS[1]);
    });

    document.head.appendChild(link);
  }

  function ensureStyles() {
    if (document.getElementById("useful-link-icon-picker-styles")) return;
    const css = `
      .ul-icon-row{margin-top:8px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
      .ul-icon-preview{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border:1px solid var(--hairline-color, #dcdcdc);border-radius:10px;background:var(--body-bg, #fff)}
      .ul-icon-preview i{font-size:18px}
      .ul-icon-preview code{font-size:12px;opacity:.8}
      .ul-icon-btn{cursor:pointer}
      .ul-icon-hint{font-size:12px;opacity:.8}
      .ul-modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;display:none;align-items:center;justify-content:center;padding:18px}
      .ul-modal{width:min(980px, 100%);max-height:min(80vh, 720px);background:#0b1220;color:#e5e7eb;border:1px solid rgba(148,163,184,.25);border-radius:16px;box-shadow:0 30px 120px rgba(0,0,0,.6);overflow:hidden;display:flex;flex-direction:column}
      .ul-modal-head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 14px;border-bottom:1px solid rgba(148,163,184,.18);background:rgba(15,23,42,.9)}
      .ul-modal-title{font-weight:700;letter-spacing:.2px}
      .ul-modal-close{background:transparent;border:1px solid rgba(148,163,184,.25);color:#e5e7eb;border-radius:10px;padding:6px 10px;cursor:pointer}
      .ul-modal-body{padding:12px 14px;display:flex;flex-direction:column;gap:10px;overflow:auto}
      .ul-search{width:100%;padding:10px 12px;border-radius:12px;border:1px solid rgba(148,163,184,.25);background:rgba(2,6,23,.55);color:#e5e7eb;outline:none}
      .ul-grid{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:8px}
      @media (max-width: 900px){.ul-grid{grid-template-columns:repeat(6,minmax(0,1fr))}}
      @media (max-width: 700px){.ul-grid{grid-template-columns:repeat(5,minmax(0,1fr))}}
      @media (max-width: 520px){.ul-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
      .ul-ic{display:flex;flex-direction:column;gap:6px;align-items:center;justify-content:center;padding:10px 6px;border-radius:12px;border:1px solid rgba(148,163,184,.18);background:rgba(2,6,23,.35);cursor:pointer;user-select:none}
      .ul-ic:hover{border-color:rgba(56,189,248,.35);background:rgba(30,64,175,.22)}
      .ul-ic i{font-size:20px}
      .ul-ic span{font-size:11px;opacity:.85;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
      .ul-count{font-size:12px;opacity:.8}
    `;
    const style = el("style", { id: "useful-link-icon-picker-styles" });
    style.textContent = css;
    document.head.appendChild(style);
  }

  function attachPicker(input) {
    ensureBootstrapIconsCss();
    ensureStyles();

    const previewIcon = el("i", { class: "bi bi-link-45deg" });
    const previewCode = el("code", { html: "bi bi-link-45deg" });
    const preview = el("div", { class: "ul-icon-preview" }, [previewIcon, previewCode]);
    const btn = el("button", { type: "button", class: "button ul-icon-btn" });
    btn.textContent = "Выбрать иконку";
    const hint = el("div", { class: "ul-icon-hint" });
    hint.innerHTML =
      'Можно ввести вручную как <code>bi bi-rocket-takeoff</code> или выбрать из списка ниже.';

    const row = el("div", { class: "ul-icon-row" }, [preview, btn]);
    input.insertAdjacentElement("afterend", hint);
    hint.insertAdjacentElement("afterend", row);

    function syncPreview() {
      const name = getIconNameFromInput(input.value) || "link-45deg";
      previewIcon.className = `bi bi-${name}`;
      previewCode.textContent = `bi bi-${name}`;
    }
    syncPreview();
    input.addEventListener("input", syncPreview);

    const backdrop = el("div", { class: "ul-modal-backdrop", role: "dialog", "aria-modal": "true" });
    const modal = el("div", { class: "ul-modal" });
    const head = el("div", { class: "ul-modal-head" });
    const title = el("div", { class: "ul-modal-title" });
    title.textContent = "Bootstrap Icons — выбор иконки";
    const close = el("button", { type: "button", class: "ul-modal-close" });
    close.textContent = "Закрыть";
    head.appendChild(title);
    head.appendChild(close);

    const body = el("div", { class: "ul-modal-body" });
    const search = el("input", { class: "ul-search", placeholder: "Поиск (например: rocket, graph, chat, translate)…", type: "search" });
    const count = el("div", { class: "ul-count" });
    const grid = el("div", { class: "ul-grid" });
    body.appendChild(search);
    body.appendChild(count);
    body.appendChild(grid);

    modal.appendChild(head);
    modal.appendChild(body);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

    function open() {
      backdrop.style.display = "flex";
      search.value = "";
      search.focus();
      renderGrid();
    }
    function hide() {
      backdrop.style.display = "none";
    }

    close.addEventListener("click", hide);
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) hide();
    });
    document.addEventListener("keydown", (e) => {
      if (backdrop.style.display === "flex" && e.key === "Escape") hide();
    });

    let icons = null;
    let iconNames = [];

    async function ensureIcons() {
      if (icons) return;
      count.textContent = "Загрузка списка иконок…";
      const json = await fetchIconsJson();
      icons = json;
      iconNames = Object.keys(json)
        .filter((k) => typeof k === "string" && k && !/^\d+$/.test(k))
        .sort();
    }

    function iconItem(name) {
      const i = el("i", { class: `bi bi-${name}` });
      const s = el("span");
      s.textContent = name;
      const it = el("div", { class: "ul-ic", title: name }, [i, s]);
      it.addEventListener("click", () => {
        setInputToIcon(input, name);
        hide();
      });
      return it;
    }

    function renderGrid() {
      if (!icons) {
        ensureIcons()
          .then(renderGrid)
          .catch(() => {
            count.innerHTML =
              'Не удалось загрузить список иконок. Открой каталог: <a href="https://icons.getbootstrap.com/" target="_blank" rel="noopener noreferrer">Bootstrap Icons</a>.';
          });
        return;
      }

      const q = (search.value || "").trim().toLowerCase();
      const filtered = q ? iconNames.filter((n) => n.includes(q)) : iconNames;
      count.textContent = `Найдено: ${filtered.length}`;
      grid.innerHTML = "";

      // render first N for performance
      const LIMIT = 320;
      const slice = filtered.slice(0, LIMIT);
      slice.forEach((n) => grid.appendChild(iconItem(n)));
      if (filtered.length > LIMIT) {
        const more = el("div", { class: "ul-icon-hint" });
        more.textContent = `Показано ${LIMIT} из ${filtered.length}. Уточни поиск, чтобы увидеть нужную иконку.`;
        grid.appendChild(more);
      }
    }

    search.addEventListener("input", renderGrid);
    btn.addEventListener("click", open);
  }

  function init() {
    const input = document.querySelector(`input[name='${INPUT_NAME}']`);
    if (!input) return;
    if (input.dataset.ulIconPickerReady === "1") return;
    input.dataset.ulIconPickerReady = "1";
    attachPicker(input);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

