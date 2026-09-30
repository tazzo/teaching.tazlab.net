// The page assembly, driven end to end: `main` boots against a jsdom document and a
// stubbed fetch, the route comes from the hash, the form comes from the descriptor in
// `fixtures/pages.json` (that fixture is pinned against /api/pages by
// `tests/test_web_fixture.py`), and the items rendered are ones the server emits
// (`fixtures/items.json`, pinned the same way).
//
// What is asserted is what a classroom would notice: the configurator is on the page,
// its choices reach the generator, and the exercise comes back drawn.

import { afterEach, beforeAll, beforeEach, describe, expect, test, vi } from "vitest";

import catalogue from "./fixtures/pages.json";
import items from "./fixtures/items.json";
import strings from "../../app/i18n/it.json";

const { main, parseRoute, pagesOf, findPage } = await import("../src/app.js");

const page = catalogue.pages.find((entry) => entry.config.length > 0);
const view = () => document.getElementById("view");
const requested = [];

/** Answer the routes app.js calls, from the fixtures, and record what was asked.
 *  A generate request is answered by the topic it names, with the fixture recorded for
 *  that topic — so a page is handed the items the server produced for it, and a page
 *  whose topic has no fixture fails loudly instead of borrowing another's items.
 *  `overrides` replaces a response by URL prefix, for the failure path. */
function stubFetch(overrides = {}) {
  return vi.fn(async (url) => {
    const path = String(url);
    requested.push(path);
    const override = Object.entries(overrides).find(([prefix]) => path.startsWith(prefix));
    if (override) return override[1];
    if (path.startsWith("/api/i18n")) return ok(strings);
    if (path.startsWith("/api/pages")) return ok(catalogue);
    const topic = new URL(path, "https://teaching.tazlab.net").searchParams.get("topic");
    const fixture = Object.values(items).find((entry) => entry.body.topic === topic);
    if (!fixture) throw new Error(`no items fixture for topic "${topic}" (${path})`);
    return ok(fixture.body);
  });
}

const ok = (body) => ({ ok: true, status: 200, json: async () => body });

const goTo = async (hash) => {
  location.hash = hash;
  // jsdom fires its own hashchange in a later task, which would re-render the page
  // after the test had begun driving it; let that land first, then render once more
  // so the nodes the test holds are the ones the app is using
  await new Promise((resolve) => setTimeout(resolve, 0));
  window.dispatchEvent(new HashChangeEvent("hashchange"));
  // render() is synchronous, but the click handler that follows is not
  await Promise.resolve();
};

// `main` runs once, not per test: every call registers another `hashchange` listener,
// and a second one would re-render the page while a test was driving it. What each test
// needs fresh is the stubbed fetch and a route, not the app.
let booted = [];
beforeAll(async () => {
  document.body.innerHTML = '<h1 id="title"><a href="#/">Didattica</a></h1><main id="view"></main>';
  // jsdom has no layout engine, so the two browser APIs the app touches are stubbed
  // here rather than worked around in the app, which must stay test-agnostic
  window.scrollTo = () => {};
  window.matchMedia = (query) => ({
    matches: false, media: query, onchange: null,
    addListener() {}, removeListener() {},
    addEventListener() {}, removeEventListener() {}, dispatchEvent: () => false,
  });
  vi.stubGlobal("fetch", stubFetch());
  await main();
  booted = [...requested];
});

beforeEach(async () => {
  vi.stubGlobal("fetch", stubFetch());
  await goTo("");
  requested.length = 0;
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the shell", () => {
  test("boots from /api/i18n and /api/pages", () => {
    expect(booted).toEqual(["/api/i18n", "/api/pages"]);
    expect(document.title).toBe(strings["ui.title"]);
    // the label goes in the anchor: that is the way back home
    expect(document.querySelector("#title a").textContent).toBe(strings["ui.title"]);
  });

  test("the home page lists the macros the catalogue serves", () => {
    const labels = [...view().querySelectorAll(".link-label")].map((node) => node.textContent);
    expect(labels).toEqual(catalogue.macros.map((macro) => strings[`macro.${macro}`]));
    expect(view().querySelectorAll('a[href="#/fisica"]')).toHaveLength(1);
  });

  test("a macro lists its sub-topics, each with the number of pages it holds", async () => {
    await goTo("#/fisica");
    const rows = [...view().querySelectorAll(".link-list li")];
    expect(rows).toHaveLength(catalogue.subs.fisica.length);
    const first = rows[0].querySelector(".link-hint").textContent;
    expect(first).toBe(`${pagesOf("fisica", catalogue.subs.fisica[0]).length} pagine`);
  });

  test("a sub-topic lists its pages, and each link routes to that page", async () => {
    await goTo("#/fisica/cinematica");
    const expected = pagesOf("fisica", "cinematica");
    expect(view().querySelectorAll(".link-list li")).toHaveLength(expected.length);
    expect(view().querySelector('a[href="#/fisica/cinematica/cinematica-problemi"]'))
      .not.toBeNull();
  });

  test("an unknown page id says so instead of rendering nothing", async () => {
    await goTo("#/fisica/cinematica/non-esiste");
    const status = view().querySelector(".status.bad");
    expect(status).not.toBeNull();
    expect(status.textContent).toContain("non-esiste");
  });

  test("parseRoute reads the three levels off the hash", async () => {
    await goTo("#/fisica/cinematica/cinematica-problemi");
    expect(parseRoute()).toEqual({ macro: "fisica", sub: "cinematica",
                                   pageId: "cinematica-problemi" });
    expect(findPage("cinematica-problemi").macro).toBe("fisica");
  });
});

describe("a page that configures its own generator", () => {
  const href = `#/${page.macro}/${page.sub}/${page.id}`;

  const openPage = async () => {
    await goTo(href);
    return view();
  };

  test("the configurator is on the page, inside the form that generates", async () => {
    const host = await openPage();
    const form = host.querySelector("form.controls");
    expect(form).not.toBeNull();
    // one field per control, the segment rows included
    expect(form.querySelectorAll(".configurator .config-field"))
      .toHaveLength(page.config.length);
    // the page pins one graph per click, so the count field the configurator drives is
    // the segment count and the exercise count field is not offered at all
    expect(form.querySelector("#count")).toBeNull();
    expect(form.querySelector(".config-rows").querySelectorAll("select"))
      .toHaveLength(page.defaults.kinds.length);
  });

  test("the served defaults are the ones the teacher sees before touching anything", async () => {
    const host = await openPage();
    const kinds = host.querySelectorAll(".config-rows select");
    expect([...kinds].map((select) => select.value))
      .toEqual(page.defaults.kinds.map(String));
    expect(host.querySelector("#seed").value).toMatch(/^\d+$/);
  });

  test("clicking Genera sends the configurator's choices and draws what comes back", async () => {
    const host = await openPage();
    // the form sends a seed, so pin it: the fixture's items are generated at a known seed
    const seedMode = host.querySelector("#seed-mode");
    seedMode.value = "number";
    seedMode.dispatchEvent(new Event("change"));
    host.querySelector("#seed").value = "4242";
    // a non-random choice, so the assertion is about what the teacher picked; the
    // control is found through its own label, not by position among the selects
    const quantityControl = page.config.find((control) => control.id === "quantity");
    const quantity = [...host.querySelectorAll(".config-field")]
      .find((field) => field.querySelector(".config-label").textContent
        === strings[quantityControl.label_key])
      .querySelector("select");
    quantity.value = quantityControl.choices[1].value;

    host.querySelector("button.controls-submit").click();
    await vi.waitFor(() => expect(host.querySelectorAll("article.card")).toHaveLength(1));

    const generate = requested.filter((url) => url.startsWith("/api/generate"));
    expect(generate.length).toBeGreaterThan(0);
    const first = new URL(generate[0], "https://teaching.tazlab.net");
    expect(first.searchParams.get("difficulty")).toBe("easy");
    expect(first.searchParams.get("seed")).toBe("4242");
    expect(first.searchParams.get("count")).toBe("1");
    // this is a graph_reading page, not graph_filling: one request, with the answer shown
    expect(first.searchParams.get("figure")).toBe("full");
    expect(generate).toHaveLength(1);
    expect(JSON.parse(first.searchParams.get("options")))
      .toEqual({ count: "3", kinds: page.defaults.kinds.map(String),
                 quantity: quantity.value, units: "random" });
    // the exercise is drawn, not just fetched: a card with a rendered graph on it
    const card = host.querySelector("article.card");
    expect(card.querySelector("svg")).not.toBeNull();
    expect(card.querySelectorAll(".steps .step").length).toBeGreaterThan(0);
    expect(card.querySelector(".answer").textContent).not.toBe("");
  });

  test("a failed generation is reported, not swallowed", async () => {
    const failing = stubFetch({
      "/api/generate": { ok: false, status: 400,
                         json: async () => ({ error: { code: "invalid_options" } }) },
    });
    vi.stubGlobal("fetch", failing);
    const host = await openPage();
    host.querySelector("button.controls-submit").click();

    await vi.waitFor(() => expect(host.querySelector("p.status.bad")).not.toBeNull());
    expect(host.querySelector("p.status").textContent).toContain("invalid_options");
    expect(host.querySelectorAll("article.card")).toHaveLength(0);
  });
});

describe("the fill-the-graph page", () => {
  const filling = catalogue.pages.find((entry) => entry.kind === "graph_filling");

  test("asks for the hidden graph first and then for its model at the same seed", async () => {
    await goTo(`#/${filling.macro}/${filling.sub}/${filling.id}`);
    const host = view();
    host.querySelector("button.controls-submit").click();
    await vi.waitFor(() => expect(host.querySelector("article.card")).not.toBeNull());

    const generate = requested.filter((url) => url.startsWith("/api/generate"))
      .map((url) => new URL(url, "https://teaching.tazlab.net"));
    // the student fills an empty grid, so the answer arrives in a second request for
    // the same item — a page that asked once would have nothing to compare against
    expect(generate).toHaveLength(2);
    expect(generate[0].searchParams.get("figure")).toBe("hidden");
    expect(generate[1].searchParams.get("figure")).toBe("full");
    expect(generate[1].searchParams.get("seed")).toBe(generate[0].searchParams.get("seed"));
    // the answer stays hidden until the teacher asks for it
    const card = host.querySelector("article.card");
    expect(card.querySelector(".figure.fillable svg")).not.toBeNull();
    expect(card.querySelector(".answer")).toBeNull();

    // the two quiet buttons are "check" and then "reveal"; the answer arrives on reveal
    card.querySelectorAll("button.btn-quiet")[1].click();
    expect(card.querySelector(".answer")).not.toBeNull();
  });
});

describe("a page without a configurator", () => {
  const plain = catalogue.pages.find((entry) => !entry.config.length
    && entry.difficulty === null && entry.count === null);

  test("offers the difficulty selector and renders a plain problem", async () => {
    await goTo(`#/${plain.macro}/${plain.sub}/${plain.id}`);
    const host = view();
    expect(host.querySelector(".configurator")).toBeNull();
    // exactly the difficulties the topic declares, not a fixed easy/medium/hard
    expect([...host.querySelectorAll("#difficulty option")].map((option) => option.value))
      .toEqual(plain.difficulties);
    expect(host.querySelector("#count")).not.toBeNull();

    host.querySelector("button.controls-submit").click();
    // one card per item the fixture for this page's topic holds
    const served = Object.values(items).find((entry) => entry.body.topic === plain.topic).body;
    await vi.waitFor(() => expect(host.querySelectorAll("article.card"))
      .toHaveLength(served.items.length));
    expect(host.querySelector("article.card .statement").textContent).not.toBe("");
  });
});
