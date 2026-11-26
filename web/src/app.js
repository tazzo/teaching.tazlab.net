// SPA: macro -> sub-topic -> page. Everything is driven by GET /api/pages, so the
import { renderConfigurator } from "./config.js";
// navigation tree lives on the server and the client only renders it.
import { renderItemForKind, renderSchedeList, el } from "./pages.js";

const state = { strings: {}, nav: null };
let strings = {};

const t = (key, fallback) => strings[key] ?? fallback ?? key;

// -------------------------------------------------------------------- routing
function parseRoute() {
  const parts = (location.hash.replace(/^#\/?/, "") || "").split("/").filter(Boolean);
  return { macro: parts[0] ?? null, sub: parts[1] ?? null, pageId: parts[2] ?? null };
}

const href = (...parts) => `#/${parts.filter(Boolean).join("/")}`;

// ---------------------------------------------------------------- the seed in the URL
// A page drawn from a seed is reproducible only if the seed can be read back. `?seed=N`
// on the address is that handle: the same address gives the same exercises, so a student
// can be sent a page, and a test can pin one. Absent, nothing changes — the worksheets
// keep their own fixed seed and a control form still rolls its own dice.
const SEED_PARAM = "seed";

function seedFromUrl() {
  const raw = new URLSearchParams(location.search).get(SEED_PARAM);
  if (raw === null || raw.trim() === "") return null;
  const value = Number(raw);
  return Number.isInteger(value) && value >= 0 ? value : null;
}

/** Write the seed that produced the batch into the address, keeping the route (the hash). */
function rememberSeed(seed) {
  if (!Number.isInteger(seed)) return;
  const url = new URL(location.href);
  if (url.searchParams.get(SEED_PARAM) === String(seed)) return;
  url.searchParams.set(SEED_PARAM, String(seed));
  history.replaceState(null, "", url);
}

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

function linkList(entries, className = "link-list") {
  const list = el("ul", className);
  entries.forEach(([label, target, hint]) => {
    const item = el("li");
    const link = el("a");
    link.href = target;
    // label and hint share one block, so the row's chevron stays on the trailing edge even
    // when the hint wraps to a line of its own on a phone
    const text = el("span", "link-text");
    text.append(el("span", "link-label", label));
    if (hint) text.append(el("span", "link-hint", hint));
    link.append(text);
    item.append(link);
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
  // The pages themselves, under the topics: a section's index is the place where a
  // student sees what there is to do, and a topic that says only "2 pagine" makes her
  // open it to find out. The list is derived from the same catalogue (`/api/pages`), so
  // it costs no second source — and a page that is not in the index is a page only its
  // author can reach.
  const pages = (state.nav?.pages ?? []).filter((page) => page.macro === macro);
  if (pages.length) {
    view.append(el("h3", "pages-heading", t("ui.pages_intro", "Le pagine di questa sezione")));
    view.append(linkList(pages.map((page) => [
      t(page.label_key, page.id), href(macro, page.sub, page.id), t(`sub.${page.sub}`, page.sub),
    ]), "page-list"));
  }
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
/** One labelled control. The label wraps the control, so the pair is a single column and
 *  the field is free of the id/first-column coupling a table-like grid forces on it. */
function controlField(labelText, control, id) {
  const field = el("label", "control-field");
  if (id) field.htmlFor = id;
  field.append(el("span", "control-label", labelText));
  field.append(control);
  return field;
}

function controls(page, reload) {
  const form = el("form", "controls");
  form.onsubmit = (event) => event.preventDefault();

  // A page whose topic declares a configurator gets one: the fields come from the
  // descriptor served by /api/pages, so this function stays page-agnostic.
  const configurator = (page.config ?? []).length
    ? renderConfigurator(page.config, page.defaults, strings)
    : null;
  if (configurator) form.append(configurator.node);

  let difficulty = page.difficulty;
  if (!difficulty) {
    const select = el("select");
    select.id = "difficulty";
    // exactly the difficulties the topic declares: not every topic has an easy level
    (page.difficulties ?? []).forEach((value) => {
      const option = el("option", null, t(`difficulty.${value}`, value));
      option.value = value;
      select.append(option);
    });
    if (select.options.length) select.value = select.options[0].value;
    form.append(controlField(t("ui.difficulty"), select, "difficulty"));
  }

  // The seed is the operator's dice: "random" (the default) draws a new one on every
  // click, so each press of Genera is a different exercise; a number pins it, and the
  // same number always comes back to the same exercise.
  const seedMode = el("select");
  seedMode.id = "seed-mode";
  [[t("ui.seed_random"), "random"], [t("ui.seed_number"), "number"]].forEach(([label, value]) => {
    const option = el("option", null, label);
    option.value = value;
    seedMode.append(option);
  });

  const seed = el("input");
  seed.id = "seed";
  seed.type = "number";
  // a seed on the address is the operator's own: it arrives pinned, not random
  const pinned = seedFromUrl();
  seed.value = String(pinned ?? Math.floor(Math.random() * 1e6));

  // A page that pins its count (a teacher asking for one graph to question a student on)
  // shows no count field: one click, one graph.
  const count = el("input");
  count.id = "count";
  count.type = "number";
  count.min = "1";
  count.max = "20";
  count.value = String(page.count ?? (page.kind === "graph_filling" ? 1 : 3));

  const submit = el("button", "btn btn-primary controls-submit", t("ui.generate"));
  submit.type = "button";
  form.append(controlField(t("ui.seed"), seedMode, "seed-mode"));
  form.append(controlField(t("ui.seed_number"), seed, "seed"));
  if (!page.count) form.append(controlField(t("ui.count"), count, "count"));
  form.append(submit);

  const randomSeed = () => {
    seed.value = String(Math.floor(Math.random() * 1e6));
  };
  if (pinned === null) randomSeed();
  const syncSeedField = () => { seed.disabled = seedMode.value === "random"; };
  if (pinned !== null) seedMode.value = "number";
  seedMode.addEventListener("change", syncSeedField);
  syncSeedField();

  const read = () => {
    const random = seedMode.value === "random";
    if (random) randomSeed();
    const chosen = Number(seed.value) || 1;
    // the batch about to be drawn is the one this address names from now on
    rememberSeed(chosen);
    return {
      difficulty: difficulty ?? form.querySelector("#difficulty")?.value ?? page.difficulties?.[0],
      seed: chosen,
      count: page.count ?? (Number(count.value) || 3),
      options: configurator ? configurator.read() : null,
    };
  };

  submit.addEventListener("click", () => reload(read()));
  return { form, read };
}

async function fetchItems(topic, difficulty, seed, count, figureMode, options) {
  const config = options ? `&options=${encodeURIComponent(JSON.stringify(options))}` : "";
  const url = `/api/generate?topic=${encodeURIComponent(topic)}&difficulty=${difficulty}` +
    `&seed=${seed}&count=${count}&figure=${figureMode}${config}`;
  const response = await fetch(url);
  const body = await response.json();
  if (!response.ok) throw new Error(body?.error?.code ?? String(response.status));
  return body.items;
}

// The exercise kinds that fill themselves on entry: a grammar worksheet shows the whole
// batch immediately, so there is no seed, no count and no "Genera" for it to wait for.
// `completion_choice` belongs here for the same reason: the German pages are a worksheet
// of eighteen cards, and a student opens them to work, not to roll a dice.
const SELF_LOADING_KINDS = new Set([
  "multiple_choice", "classification_choice", "completion_choice",
]);

function renderPage(macro, sub, page) {
  const view = el("section", "page");
  view.append(crumb([
    [t("nav.home"), href()], [t(`macro.${macro}`, macro), href(macro)],
    [t(`sub.${sub}`, sub), href(macro, sub)], [t(page.label_key, page.id), null],
  ]));
  view.append(el("h2", null, t(page.label_key, page.id)));
  view.append(el("p", "kind-tag", t(`kind.${page.kind}`, page.kind)));
  // The page's own short explanation in Italian, above the exercises: three to six lines
  // with the examples in German. It is the server's words (an i18n key on the page), so a
  // page without one draws nothing rather than an empty box.
  const intro = page.intro_key ? t(page.intro_key, "") : "";
  if (intro) view.append(el("p", "page-intro", intro));

  const status = el("p", "status");
  const results = el("main", "results");

  // The sheets are not generated: the list is the server's (`/api/schede`, built from
  // schede/schede.json), so a new sheet appears here by being published and not by
  // touching this file. No controls, no seed, nothing to answer.
  if (page.kind === "schede_list") {
    view.append(status);
    view.append(results);
    view.append(el("p", "scheda-hint", t("ui.schede_next")));
    const load = async () => {
      status.textContent = t("ui.schede_loading", "Caricamento…");
      status.classList.remove("bad");
      try {
        const body = await (await fetch("/api/schede")).json();
        results.replaceChildren();
        status.textContent = "";
        const schede = body.schede ?? [];
        if (!schede.length) {
          status.textContent = t("ui.schede_empty");
          return;
        }
        results.append(renderSchedeList(schede, { strings }));
      } catch (error) {
        console.error("schede failed", error);
        status.textContent = `${t("ui.error")}: ${error?.message ?? error}`;
        status.classList.add("bad");
      }
    };
    load();
    return view;
  }

  // For multiple_choice grammar worksheets, show all questions immediately without
  // needing random seed, count picker or clicking "Genera". The kind that asks the student
  // to name the sentence type first loads the same way: the lock is on each card.
  if (SELF_LOADING_KINDS.has(page.kind)) {
    const loadExercises = async () => {
      status.textContent = t("ui.loading", "Caricamento...");
      status.classList.remove("bad");
      results.replaceChildren();
      try {
        const count = page.count ?? 20;
        const difficulty = page.difficulty ?? "easy";
        // the seed on the address, when there is one: the same link gives the same page
        const seed = seedFromUrl() ?? 1;
        const items = await fetchItems(page.topic, difficulty, seed, count, "full", null);
        status.textContent = "";
        items.forEach((item, index) => {
          results.append(renderItemForKind(page.kind, item, index, { strings, page }));
        });
      } catch (error) {
        console.error("fetch failed", error);
        status.textContent = `${t("ui.error")}: ${error?.message ?? error}`;
        status.classList.add("bad");
      }
    };
    loadExercises();
    view.append(status, results);
    return view;
  }

  const { form, read } = controls(page, async ({ difficulty, seed, count, options }) => {
    status.textContent = t("ui.loading");
    status.classList.remove("bad");
    results.replaceChildren();
    try {
      // graph_filling needs an empty grid (the model comes in a second request); a mill
      // page needs the drawing alone — the server is what strips the marker naming the
      // asked instant and the labels naming the kind of motion
      const mode = page.kind === "graph_filling" ? "hidden"
        : page.bare_graph ? "bare" : "full";
      const items = await fetchItems(page.topic, difficulty, seed, count, mode, options);
      if (page.kind === "graph_filling" && items.length) {
        // the model for the same item: same topic/difficulty/seed/index, full figure
        const model = (await fetchItems(page.topic, difficulty, seed, 1, "full", options))[0];
        status.textContent = "";
        results.append(renderItemForKind(page.kind, items[0], 0, { strings, model }));
        return;
      }
      status.textContent = "";
      items.forEach((item, index) => {
        results.append(renderItemForKind(page.kind, item, index, { strings, page }));
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
function renderTopnav(currentMacro) {
  const nav = document.getElementById("topnav");
  if (!nav) return;
  nav.replaceChildren(
    ...(state.nav?.macros ?? []).map((macro) => {
      const a = el("a", null, t(`macro.${macro}`, macro));
      a.href = href(macro);
      if (macro === currentMacro) a.classList.add("active");
      return a;
    })
  );
}

function render() {
  const route = parseRoute();
  renderTopnav(route.macro);
  const host = document.getElementById("view");
  let content;
  if (!route.macro) content = renderHome();
  else if (!route.sub) {
    // A section that holds exactly one page opens it directly: the sheets are one page,
    // and a topic level saying "1 pagine" between the menu and it would be a click that
    // exists only for the shape of the data. Every other section keeps its index.
    const subsOfMacro = state.nav?.subs?.[route.macro] ?? [];
    const pagesOfMacro = (state.nav?.pages ?? []).filter((page) => page.macro === route.macro);
    content = (subsOfMacro.length === 1 && pagesOfMacro.length === 1)
      ? renderPage(route.macro, pagesOfMacro[0].sub, pagesOfMacro[0])
      : renderMacro(route.macro);
  }
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
  // write the label into the anchor, not over it: the title is the way back home
  const brand = document.querySelector("#title a") ?? document.getElementById("title");
  brand.textContent = t("ui.title");
  state.nav = await (await fetch("/api/pages")).json();
  window.addEventListener("hashchange", render);
  render();
}

// The bootstrap is deferred behind a guard so the module can be imported without
// starting the app: the suite drives `main` against a jsdom document and a stubbed
// fetch, and a module that fired on import would race the test for the same DOM.
// Vite folds the flag away in a build, so the browser runs exactly what it ran before.
if (!import.meta.env?.VITEST) {
  main().catch((error) => {
    document.getElementById("view").textContent = `Avvio: ${error}`;
  });
}

// What the suite needs to reach; everything else it exercises through `main` and the
// DOM, which is the path a teacher takes.
export { main, parseRoute, pagesOf, findPage };
