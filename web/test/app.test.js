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
    const target = new URL(path, "https://teaching.tazlab.net");
    const topic = target.searchParams.get("topic");
    const figure = target.searchParams.get("figure");
    // the payload the URL asks for, when there is one: a mill page must be handed the bare
    // drawing, or the suite would certify a page the server never serves
    const fixture = (figure && items[figure]?.body.topic === topic
      ? items[figure]
      : Object.values(items).find((entry) => entry.body.topic === topic));
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
    // a mill page asks for the drawing alone: the marker that named the asked instant and
    // the labels that named the kind of motion are the server's to strip, not the client's
    expect(first.searchParams.get("figure")).toBe("bare");
    expect(generate).toHaveLength(1);
    expect(JSON.parse(first.searchParams.get("options")))
      .toEqual({ count: "3", kinds: page.defaults.kinds.map(String),
                 quantity: quantity.value, units: "random" });
    // the graph is drawn, and the card is the graph and nothing else: the teacher asks
    const card = host.querySelector("article.card");
    expect(card.querySelector("svg")).not.toBeNull();
    expect(card.querySelector(".statement")).toBeNull();
    expect(card.querySelector(".steps")).toBeNull();
    expect(card.querySelector(".answer")).toBeNull();
    expect(card.querySelector(".figure-legend")).toBeNull();
    // and nothing on the graph either: the asked instant is the question, and there is none
    const drawn = [...card.querySelectorAll("text")].map((node) => node.textContent);
    expect(drawn).not.toContain(strings["marker.asked_instant"]);
    expect(drawn).not.toContain(strings["marker.asked_segment"]);
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

// --- the page where the kind of sentence is chosen -------------------------
// The operator rejected the previous page because the classification written in every
// option ("who (defining)") repeats the right kind four times: it can be read off the
// pattern without looking at the commas. This page asks the kind separately, under the
// sentence, and the check is disabled until one is chosen. What is asserted here is that
// interaction, on the cards the server really sends (`fixtures/items.json` is pinned
// against `/api/generate` by `tests/test_web_fixture.py`), card by card: a disabled state
// before the click, not an error after it.

describe("the page where the sentence's kind is chosen", () => {
  const classifying = catalogue.pages.find((entry) => entry.kind === "classification_choice");
  // the batch the page asks for, as the server produced it (one entry per exercise)
  const batch = items.classification.body.items;

  const open = async () => {
    await goTo(`#/${classifying.macro}/${classifying.sub}/${classifying.id}`);
    await vi.waitFor(() => expect(view().querySelectorAll("article.card"))
      .toHaveLength(batch.length));
    return [...view().querySelectorAll("article.card")];
  };

  const kindButtons = (card) => [...card.querySelectorAll("button.classification-option")];
  const kindButton = (card, value) =>
    card.querySelector(`button.classification-option[data-classification="${value}"]`);
  const optionButton = (card, text) =>
    [...card.querySelectorAll(".choice-option")]
      .find((button) => button.querySelector(".choice-text").textContent.trim() === text);
  const otherKind = (value) => (value === "defining" ? "non-defining" : "defining");

  test("loads its own batch, with no form and no generate button", async () => {
    await open();
    expect(view().querySelector("form.controls")).toBeNull();
    const generate = requested.filter((url) => url.startsWith("/api/generate"));
    // the harness renders the page twice (jsdom fires its own hashchange, then the test
    // dispatches one); the same batch is asked twice, identically — one URL, not two
    expect(new Set(generate).size).toBe(1);
    const url = new URL(generate[0], "https://teaching.tazlab.net");
    expect(url.searchParams.get("topic")).toBe(classifying.topic);
    expect(url.searchParams.get("count")).toBe("20");
    expect(url.searchParams.get("seed")).toBe("1");
    expect(url.searchParams.get("figure")).toBe("full");
  });

  test("twenty cards, twenty distinct sentences", async () => {
    const cards = await open();
    expect(cards).toHaveLength(20);
    const statements = cards.map((card) => card.querySelector(".statement").textContent.trim());
    expect(new Set(statements).size).toBe(20);
  });

  test("no option and no sentence carries the classification", async () => {
    const cards = await open();
    for (const card of cards) {
      expect(card.querySelector(".statement").textContent).not.toContain("(");
      expect(card.querySelector(".statement").textContent).not.toMatch(/defining/i);
      for (const option of card.querySelectorAll(".choice-text")) {
        expect(option.textContent).not.toContain("(");
        expect(option.textContent).not.toMatch(/defining/i);
      }
      // and the card never prints the answer the selector is asking for
      expect(card.textContent).not.toMatch(/\(\s*(non-)?defining\s*\)/i);
    }
  });

  test("a selector with the two kinds sits under the sentence, above the pronouns", async () => {
    const [card] = await open();
    const picker = card.querySelector(".classification-picker");
    expect(picker).not.toBeNull();
    expect(picker.querySelector(".classification-prompt").textContent)
      .toBe(strings["ui.classification_prompt"]);
    expect(kindButtons(card).map((button) => button.dataset.classification))
      .toEqual(["defining", "non-defining"]);
    expect(kindButtons(card).map((button) => button.textContent))
      .toEqual([strings["ui.classification_defining"], strings["ui.classification_non_defining"]]);
    expect(card.innerHTML.indexOf("classification-picker"))
      .toBeLessThan(card.innerHTML.indexOf("choice-list"));
  });

  test("every card opens with the check disabled, and says why", async () => {
    const cards = await open();
    for (const card of cards) {
      const check = card.querySelector(".page-actions button");
      expect(check.disabled).toBe(true);
      expect(check.getAttribute("aria-disabled")).toBe("true");
      const hint = card.querySelector(".classification-hint");
      expect(hint.hidden).toBe(false);
      expect(hint.textContent).toBe(strings["ui.classification_locked"]);
    }
  });

  test("choosing the pronoun does not unlock the check; choosing the kind does", async () => {
    const [card] = await open();
    const check = card.querySelector(".page-actions button");
    const expected = batch[0].answer.payload;
    optionButton(card, expected.correct[0]).click();
    expect(check.disabled).toBe(true);            // still locked: the kind is the key

    kindButton(card, expected.classification[0]).click();
    expect(check.disabled).toBe(false);
    expect(check.getAttribute("aria-disabled")).toBe("false");
    expect(card.querySelector(".classification-hint").hidden).toBe(true);

    // pointing the selector at the other kind keeps the check available
    kindButton(card, otherKind(expected.classification[0])).click();
    expect(kindButton(card, otherKind(expected.classification[0]))
      .getAttribute("aria-checked")).toBe("true");
    expect(kindButton(card, expected.classification[0]).getAttribute("aria-checked")).toBe("false");
    expect(check.disabled).toBe(false);
  });

  test("the right pronoun with the wrong kind is wrong, and only the kind is reported", async () => {
    const [card] = await open();
    const expected = batch[0].answer.payload;
    optionButton(card, expected.correct[0]).click();
    kindButton(card, otherKind(expected.classification[0])).click();
    card.querySelector(".page-actions button").click();

    const status = card.querySelector(".choice-status");
    expect(status.className).toContain("bad");
    expect(status.textContent).toContain(strings["ui.incorrect"]);
    expect(status.textContent).toContain(strings["ui.classification_wrong"]);
    expect(status.textContent).not.toContain(strings["ui.pronoun_wrong"]);
    expect(status.textContent).toContain(expected.explanation[0].slice(0, 30));
    // the selector shows which kind was right, and the card cannot be re-answered
    expect(kindButton(card, expected.classification[0])
      .classList.contains("classification-correct")).toBe(true);
    expect(kindButton(card, otherKind(expected.classification[0]))
      .classList.contains("classification-incorrect")).toBe(true);
    expect(kindButtons(card).every((button) => button.disabled)).toBe(true);
  });

  test("the wrong pronoun with the right kind reports the pronoun", async () => {
    const [card] = await open();
    const expected = batch[0].answer.payload;
    const wrong = expected.options.find((option) => option !== expected.correct[0]);
    optionButton(card, wrong).click();
    kindButton(card, expected.classification[0]).click();
    card.querySelector(".page-actions button").click();
    const status = card.querySelector(".choice-status");
    expect(status.className).toContain("bad");
    expect(status.textContent).toContain(strings["ui.pronoun_wrong"]);
    expect(status.textContent).not.toContain(strings["ui.classification_wrong"]);
  });

  test("both answers right is correct, and every card of the batch can be answered", async () => {
    const cards = await open();
    cards.forEach((card, index) => {
      const expected = batch[index].answer.payload;
      optionButton(card, expected.correct[0]).click();
      kindButton(card, expected.classification[0]).click();
      card.querySelector(".page-actions button").click();
      const status = card.querySelector(".choice-status");
      expect(status.className).toContain("good");
      expect(status.textContent).toContain(strings["ui.correct"]);
    });
    // the batch exercises both kinds, or the selector would have one answer
    expect(new Set(batch.map((item) => item.answer.payload.classification[0])))
      .toEqual(new Set(["defining", "non-defining"]));
  });

  test("a second attempt starts locked again", async () => {
    const [card] = await open();
    const expected = batch[0].answer.payload;
    optionButton(card, expected.correct[0]).click();
    kindButton(card, expected.classification[0]).click();
    const [check, retry] = card.querySelectorAll(".page-actions button");
    check.click();
    retry.click();
    expect(check.disabled).toBe(true);
    expect(card.querySelector(".classification-hint").hidden).toBe(false);
    expect(kindButtons(card).map((button) => button.getAttribute("aria-checked")))
      .toEqual(["false", "false"]);
  });

  test("the same sentence drawn as a plain multiple choice has no selector: the rest is untouched", async () => {
    const { renderItemForKind } = await import("../src/pages.js");
    const plain = renderItemForKind("multiple_choice", batch[0], 0,
      { strings, page: { kind: "multiple_choice" } });
    document.body.append(plain);
    expect(plain.querySelector(".classification-picker")).toBeNull();
    expect(plain.querySelector(".classification-hint")).toBeNull();
    expect(plain.querySelector(".page-actions button").disabled).toBe(false);
    plain.remove();
  });
});

// --- the same interaction, a second grammar --------------------------------
// The operator asked for a *page* (not a PDF) on the present perfect simple against the
// continuous, with the interaction the site already had: the kind is chosen first and the
// check is born disabled. The kind is not the same question as on the relative page — it is
// the class of the verb ("azione" or "stato"), and only after that the form — so what is
// asserted here is that the picker comes from the payload and not from the client: the same
// renderer, a different prompt, a different pair of values, a different wrong-answer line.
// The batch is the one the server sends (`fixtures/items.json`, pinned by
// `tests/test_web_fixture.py`).

describe("the page where the kind of the verb is chosen, then the form", () => {
  const page = catalogue.pages.find(
    (entry) => entry.topic === "english.grammar.present_perfect_simple_continuous");
  const batch = items.classification_verb.body.items;

  const open = async () => {
    await goTo(`#/${page.macro}/${page.sub}/${page.id}`);
    await vi.waitFor(() => expect(view().querySelectorAll("article.card"))
      .toHaveLength(batch.length));
    return [...view().querySelectorAll("article.card")];
  };

  const kindButtons = (card) => [...card.querySelectorAll("button.classification-option")];
  const kindButton = (card, value) =>
    card.querySelector(`button.classification-option[data-classification="${value}"]`);
  const optionButton = (card, text) =>
    [...card.querySelectorAll(".choice-option")]
      .find((button) => button.querySelector(".choice-text").textContent.trim() === text);

  test("it is a catalogue page of its own, with twenty cards and no configurator", async () => {
    expect(page).toBeTruthy();
    expect(page.kind).toBe("classification_choice");
    expect(page.difficulty).toBe("medium");
    await open();
    expect(view().querySelector("form.controls")).toBeNull();
    const generate = requested.filter((url) => url.startsWith("/api/generate"));
    expect(new Set(generate).size).toBe(1);
    const url = new URL(generate[0], "https://teaching.tazlab.net");
    expect(url.searchParams.get("topic")).toBe(page.topic);
    expect(url.searchParams.get("count")).toBe("20");
    expect(url.searchParams.get("seed")).toBe("1");
  });

  test("twenty cards, twenty distinct sentences, and no card prints its own kind", async () => {
    const cards = await open();
    expect(cards).toHaveLength(20);
    const statements = cards.map((card) => card.querySelector(".statement").textContent.trim());
    expect(new Set(statements).size).toBe(20);
    for (const card of cards) {
      const statement = card.querySelector(".statement").textContent;
      // the hint in the statement names the verb; the kind is never written beside it
      expect(statement).not.toMatch(/\b(azione|stato|action|state)\b/i);
      for (const option of card.querySelectorAll(".choice-text")) {
        expect(option.textContent).not.toMatch(/\b(azione|stato|action|state)\b/i);
      }
    }
  });

  test("the picker asks about the verb, with the payload's two values", async () => {
    const [card] = await open();
    const picker = card.querySelector(".classification-picker");
    expect(picker.querySelector(".classification-prompt").textContent)
      .toBe(strings["ui.classification_prompt_verb"]);
    // ... which is not the question the relative page asks
    expect(strings["ui.classification_prompt_verb"])
      .not.toBe(strings["ui.classification_prompt"]);
    expect(kindButtons(card).map((button) => button.dataset.classification))
      .toEqual(["action", "state"]);
    expect(kindButtons(card).map((button) => button.textContent))
      .toEqual([strings["ui.classification_verb_action"],
                strings["ui.classification_verb_state"]]);
    expect(card.innerHTML.indexOf("classification-picker"))
      .toBeLessThan(card.innerHTML.indexOf("choice-list"));
  });

  test("every card opens locked, and the lock speaks about the verb, not the relative", async () => {
    const cards = await open();
    for (const card of cards) {
      const check = card.querySelector(".page-actions button");
      expect(check.disabled).toBe(true);
      const hint = card.querySelector(".classification-hint");
      expect(hint.hidden).toBe(false);
      // the card's own payload decides the wording: a verb card cannot borrow the line
      // written for a relative clause
      const payload = batch[cards.indexOf(card)].answer.payload;
      expect(hint.textContent).toBe(strings[payload.classification_locked_key[0]]);
    }
  });

  test("the form does not unlock the check; the kind does", async () => {
    const [card] = await open();
    const check = card.querySelector(".page-actions button");
    const expected = batch[0].answer.payload;
    optionButton(card, expected.correct[0]).click();
    expect(check.disabled).toBe(true);            // still locked: the kind is the key
    kindButton(card, expected.classification[0]).click();
    expect(check.disabled).toBe(false);
    expect(card.querySelector(".classification-hint").hidden).toBe(true);
  });

  test("the right form with the wrong kind is wrong, and only the kind is reported", async () => {
    const [card] = await open();
    const expected = batch[0].answer.payload;
    const other = expected.classification[0] === "action" ? "state" : "action";
    optionButton(card, expected.correct[0]).click();
    kindButton(card, other).click();
    card.querySelector(".page-actions button").click();

    const status = card.querySelector(".choice-status");
    expect(status.className).toContain("bad");
    expect(status.textContent).toContain(strings["ui.classification_wrong_verb"]);
    expect(status.textContent).not.toContain(strings["ui.form_wrong"]);
    expect(status.textContent).not.toContain(strings["ui.classification_wrong"]);
  });

  test("both facts right is right, and the explanation is the one the server sent", async () => {
    const [card] = await open();
    const expected = batch[0].answer.payload;
    optionButton(card, expected.correct[0]).click();
    kindButton(card, expected.classification[0]).click();
    card.querySelector(".page-actions button").click();

    const status = card.querySelector(".choice-status");
    expect(status.className).toContain("good");
    expect(status.textContent).toContain(expected.explanation[0].slice(0, 30));
    expect(card.querySelectorAll(".page-actions button")[0].style.display).toBe("none");
  });
});
