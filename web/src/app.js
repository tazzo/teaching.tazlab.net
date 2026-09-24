// SPA: macro -> sub-topic -> page. Everything is driven by GET /api/pages, so the
// navigation tree lives on the server and the client only renders it.
import { renderItemForKind, el } from "./pages.js";

const state = { strings: {}, nav: null };
let strings = {};

const t = (key, fallback) => strings[key] ?? fallback ?? key;

// -------------------------------------------------------------------- routing
function parseRoute() {
  const parts = (location.hash.replace(/^#\/?/, "") || "").split("/").filter(Boolean);
  return { macro: parts[0] ?? null, sub: parts[1] ?? null, pageId: parts[2] ?? null };
}

const href = (...parts) => `#/${parts.filter(Boolean).join("/")}`;

function pagesOf(macro, sub) {
  return (state.nav?.pages ?? []).filter((page) => page.macro === macro && page.sub === sub);
}

function findPage(pageId) {
  return (state.nav?.pages ?? []).find((page) => page.id === pageId);
}

// --------------------------------------------------------------------- layout
function crumb(pairs) {
  const nav = el("nav", "crumbs");
  pairs.forEach(([label, target], index) => {
    if (index) nav.append(el("span", "crumb-sep", "\u203a"));
    if (target) {
      const link = el("a", null, label);
      link.href = target;
      nav.append(link);
    } else {
      nav.append(el("strong", null, label));
    }
  });
  return nav;
}

function linkList(entries) {
  const list = el("ul", "link-list");
  entries.forEach(([label, target, hint]) => {
    const item = el("li");
    const link = el("a", null, label);
    link.href = target;
    item.append(link);
    if (hint) item.append(el("span", "hint", hint));
    list.append(item);
  });
  return list;
}

function renderHome() {
  const view = el("section", "page");
  view.append(el("h2", null, t("ui.home_intro")));
  view.append(linkList((state.nav?.macros ?? []).map((macro) => [
    t(`macro.${macro}`, macro), href(macro),
    (state.nav?.subs?.[macro] ?? []).map((sub) => t(`sub.${sub}`, sub)).join(" · "),
  ])));
  return view;
}

function renderMacro(macro) {
  const view = el("section", "page");
  view.append(crumb([[t("nav.home"), href()], [t(`macro.${macro}`, macro), null]]));
  view.append(el("h2", null, t("ui.macro_intro")));
  view.append(linkList((state.nav?.subs?.[macro] ?? []).map((sub) => {
    const count = pagesOf(macro, sub).length;
    return [t(`sub.${sub}`, sub), href(macro, sub), `${count} pagine`];
  })));
  return view;
}

function renderSub(macro, sub) {
  const view = el("section", "page");
  view.append(crumb([
    [t("nav.home"), href()], [t(`macro.${macro}`, macro), href(macro)], [t(`sub.${sub}`, sub), null],
  ]));
  view.append(el("h2", null, t("ui.sub_intro")));
  view.append(linkList(pagesOf(macro, sub).map((page) => [
    t(page.label_key, page.id), href(macro, sub, page.id), t(`kind.${page.kind}`, page.kind),
  ])));
  return view;
}

// ---------------------------------------------------------------- page itself
function controls(page, reload) {
  const form = el("form", "controls");
  form.onsubmit = (event) => event.preventDefault();

  let difficulty = page.difficulty;
  if (!difficulty) {
    const label = el("label", null, t("ui.difficulty"));
    label.htmlFor = "difficulty";
    const select = el("select");
    select.id = "difficulty";
    // exactly the difficulties the topic declares: not every topic has an easy level
    (page.difficulties ?? []).forEach((value) => {
      const option = el("option", null, t(`difficulty.${value}`, value));
      option.value = value;
      select.append(option);
    });
    if (select.options.length) select.value = select.options[0].value;
    form.append(label, select);
  }

  const seedLabel = el("label", null, t("ui.seed"));
  seedLabel.htmlFor = "seed";
  const seed = el("input");
  seed.id = "seed";
  seed.type = "number";
  seed.value = String(Math.floor(Math.random() * 1e6));

  const countLabel = el("label", null, t("ui.count"));
  countLabel.htmlFor = "count";
  const count = el("input");
  count.id = "count";
  count.type = "number";
  count.min = "1";
  count.max = "20";
  count.value = page.kind === "graph_filling" ? "1" : "3";

  const submit = el("button", null, t("ui.generate"));
  submit.type = "button";
  form.append(seedLabel, seed, countLabel, count, submit);

  const read = () => ({
    difficulty: difficulty ?? form.querySelector("#difficulty")?.value ?? page.difficulties?.[0],
    seed: Number(seed.value) || 1,
    count: Number(count.value) || 3,
  });

  submit.addEventListener("click", () => reload(read()));
  return { form, read };
}

async function fetchItems(topic, difficulty, seed, count, figureMode) {
  const url = `/api/generate?topic=${encodeURIComponent(topic)}&difficulty=${difficulty}` +
    `&seed=${seed}&count=${count}&figure=${figureMode}`;
  const response = await fetch(url);
  const body = await response.json();
  if (!response.ok) throw new Error(body?.error?.code ?? String(response.status));
  return body.items;
}

function renderPage(macro, sub, page) {
  const view = el("section", "page");
  view.append(crumb([
    [t("nav.home"), href()], [t(`macro.${macro}`, macro), href(macro)],
    [t(`sub.${sub}`, sub), href(macro, sub)], [t(page.label_key, page.id), null],
  ]));
  view.append(el("h2", null, t(page.label_key, page.id)));
  view.append(el("p", "kind-tag", t(`kind.${page.kind}`, page.kind)));

  const status = el("p", "status");
  const results = el("main", "results");

  const { form, read } = controls(page, async ({ difficulty, seed, count }) => {
    status.textContent = t("ui.loading");
    status.classList.remove("bad");
    results.replaceChildren();
    try {
      const mode = page.kind === "graph_filling" ? "hidden" : "full";
      const items = await fetchItems(page.topic, difficulty, seed, count, mode);
      if (page.kind === "graph_filling" && items.length) {
        // the model for the same item: same topic/difficulty/seed/index, full figure
        const model = (await fetchItems(page.topic, difficulty, seed, 1, "full"))[0];
        status.textContent = "";
        results.append(renderItemForKind(page.kind, items[0], 0, { strings, model }));
        return;
      }
      status.textContent = "";
      items.forEach((item, index) => {
        results.append(renderItemForKind(page.kind, item, index, { strings }));
      });
    } catch (error) {
      // log the real thing for the console, show a short message to the user
      console.error("generate failed", error);
      status.textContent = `${t("ui.error")}: ${error?.message ?? error}`;
      status.classList.add("bad");
    }
  });

  view.append(form, status, results);
  return view;
}

// ---------------------------------------------------------------------- shell
function render() {
  const route = parseRoute();
  const host = document.getElementById("view");
  let content;
  if (!route.macro) content = renderHome();
  else if (!route.sub) content = renderMacro(route.macro);
  else if (!route.pageId) content = renderSub(route.macro, route.sub);
  else {
    const page = findPage(route.pageId);
    content = page ? renderPage(route.macro, route.sub, page)
      : el("p", "status bad", `${t("ui.error")}: ${route.pageId}`);
  }
  host.replaceChildren(content);
  window.scrollTo({ top: 0 });
}

async function main() {
  strings = await (await fetch("/api/i18n")).json();
  document.title = t("ui.title");
  document.getElementById("title").textContent = t("ui.title");
  state.nav = await (await fetch("/api/pages")).json();
  window.addEventListener("hashchange", render);
  render();
}

main().catch((error) => {
  document.getElementById("view").textContent = `Avvio: ${error}`;
});
