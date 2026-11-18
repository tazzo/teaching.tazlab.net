// The German section, driven end to end in jsdom: the index the catalogue serves, the
// intro, and the two ways of answering a card — the field typed in, the options clicked —
// with the reason appearing only after the answer.
//
// The fixtures are the server's: `pages.json` is pinned against /api/pages and
// `items.json` against /api/generate by `tests/test_web_fixture.py`, so these tests can
// only pass on cards the site really serves. What is asserted is what a girl of ten would
// notice: the cards are all there, the field takes the answer (and its `ss` spelling), a
// wrong answer says what the right one was and why, and the index reaches every page.

import { readFileSync } from "node:fs";

import { afterEach, beforeAll, beforeEach, describe, expect, test, vi } from "vitest";

import catalogue from "./fixtures/pages.json";
import items from "./fixtures/items.json";
import strings from "../../app/i18n/it.json";

const { main, findPage } = await import("../src/app.js");

const view = () => document.getElementById("view");
const requested = [];

const ok = (body) => ({ ok: true, status: 200, json: async () => body });

/** Answer the three routes app.js calls, from the fixtures, and record what was asked. */
function stubFetch() {
  return vi.fn(async (url) => {
    const path = String(url);
    requested.push(path);
    if (path.startsWith("/api/i18n")) return ok(strings);
    if (path.startsWith("/api/pages")) return ok(catalogue);
    const target = new URL(path, "https://teaching.tazlab.net");
    const topic = target.searchParams.get("topic");
    const fixture = Object.values(items).find((entry) => entry.body.topic === topic);
    if (!fixture) throw new Error(`no items fixture for topic "${topic}"`);
    return ok(fixture.body);
  });
}

const goTo = async (hash, search = "") => {
  // the address is rebuilt on every navigation: a seed one test pinned is that test's,
  // and a page opened with no parameter is opened the way a browser opens it
  history.replaceState(null, "", `${location.pathname}${search}`);
  location.hash = hash;
  await new Promise((resolve) => setTimeout(resolve, 0));
  window.dispatchEvent(new HashChangeEvent("hashchange"));
  await Promise.resolve();
};

// the page as the catalogue serves it, read from the pinned fixture (the app's own
// `findPage` only knows what `/api/pages` handed it after boot)
const PAGE = catalogue.pages.find((page) => page.id === "tedesco-1a-laender-kommen");
const HREF = `#/${PAGE.macro}/${PAGE.sub}/${PAGE.id}`;
const BATCH = items.german_completion.body.items;

const openPage = async () => {
  await goTo(HREF);
  await vi.waitFor(() => expect(view().querySelectorAll("article.card")).toHaveLength(18));
  return [...view().querySelectorAll("article.card")];
};

/** A card's field, its check button and its status line. */
const fieldOf = (card) => card.querySelector("input.completion-input");
const checkOf = (card) => card.querySelector('button[type="submit"]');
const retryOf = (card) => [...card.querySelectorAll("button")].find((b) => b.textContent === strings["ui.try_again"]);
const statusOf = (card) => card.querySelector(".choice-status");

const completionCard = (cards) => cards.find((card) => fieldOf(card));
const choiceCard = (cards) => cards.find((card) => !fieldOf(card));

const typeAndCheck = (card, value, { enter = false } = {}) => {
  const field = fieldOf(card);
  field.value = value;
  if (enter) {
    // jsdom has no implicit form submission: the browser submits the form when Enter is
    // pressed in a text field, and here what is driven is exactly the event that results
    card.querySelector("form.completion-form")
      .dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
  } else {
    checkOf(card).click();
  }
};

beforeAll(async () => {
  document.body.innerHTML =
    '<h1 id="title"><a href="#/">Didattica</a></h1><nav id="topnav"></nav><main id="view"></main>';
  window.scrollTo = () => {};
  window.matchMedia = (query) => ({
    matches: false, media: query, onchange: null,
    addListener() {}, removeListener() {},
    addEventListener() {}, removeEventListener() {}, dispatchEvent: () => false,
  });
  vi.stubGlobal("fetch", stubFetch());
  await main();
});

beforeEach(async () => {
  await goTo("");
  requested.length = 0;
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.stubGlobal("fetch", stubFetch());
});


describe("the section is in the index", () => {
  test("«Tedesco» is a voice of the top bar, and it leads to the section", async () => {
    await goTo("");
    const links = [...document.querySelectorAll("#topnav a")];
    const german = links.find((a) => a.textContent === strings["macro.tedesco"]);
    expect(german).toBeTruthy();
    expect(german.getAttribute("href")).toBe("#/tedesco");
  });

  test("the section index lists the four topics and the five pages", async () => {
    await goTo("#/tedesco");
    const topics = [...view().querySelectorAll(".link-list li .link-label")]
      .map((node) => node.textContent);
    expect(topics).toEqual(catalogue.subs.tedesco.map((sub) => strings[`sub.${sub}`]));
    expect(topics).toHaveLength(4);

    const pages = [...view().querySelectorAll(".page-list a")];
    expect(pages).toHaveLength(5);
    // the label, not the whole anchor: the anchor also carries the topic it belongs to
    expect(pages.map((a) => a.querySelector(".link-label").textContent))
      .toContain(strings["page.tedesco.unit1b_possessivi"]);
    expect(pages.map((a) => a.getAttribute("href"))).toContain(
      "#/tedesco/1a/tedesco-1a-laender-kommen");
  });

  test("each of the five pages opens on its own cards", async () => {
    for (const id of ["tedesco-1a-laender-kommen", "tedesco-1b-artikel",
      "tedesco-1b-possessivi", "tedesco-1c-familie", "tedesco-zahlen"]) {
      const page = findPage(id);
      await goTo(`#/${page.macro}/${page.sub}/${page.id}`);
      await vi.waitFor(() => expect(view().querySelectorAll("article.card")).toHaveLength(18));
    }
  });
});

describe("a page of the German section", () => {
  test("opens with the short explanation in Italian, examples in German", async () => {
    await openPage();
    const intro = view().querySelector(".page-intro");
    expect(intro).not.toBeNull();
    expect(intro.textContent).toBe(strings[PAGE.intro_key]);
    expect(intro.textContent).toContain("Ich komme aus");
    expect(intro.textContent.split("\n").filter((line) => line.trim()).length).toBeGreaterThanOrEqual(3);
  });

  test("loads its whole batch with no form and no generate button", async () => {
    await openPage();
    expect(view().querySelector("form.controls")).toBeNull();
    const generate = requested.filter((url) => url.startsWith("/api/generate"));
    expect(new Set(generate).size).toBe(1);
    const url = new URL(generate[0], "https://teaching.tazlab.net");
    expect(url.searchParams.get("topic")).toBe(PAGE.topic);
    expect(url.searchParams.get("count")).toBe("18");
  });

  test("holds both formats, and every sentence carries the gap", async () => {
    const cards = await openPage();
    expect(cards.filter((card) => fieldOf(card))).toHaveLength(9);
    expect(cards.filter((card) => !fieldOf(card))).toHaveLength(9);
    for (const card of cards) {
      expect(card.querySelector(".statement").textContent).toContain("______");
    }
    const statements = cards.map((card) => card.querySelector(".statement").textContent.trim());
    expect(new Set(statements).size).toBe(18);
  });

  test("no card prints its solution in the sentence", async () => {
    const cards = await openPage();
    cards.forEach((card, index) => {
      const sentence = card.querySelector(".statement").textContent.toLowerCase();
      const solution = BATCH[index].answer.payload.correct[0].toLowerCase();
      // whole words, as the server's verifier does: «den» is a substring of «Niederlanden»
      // and that is not the answer written in the sentence
      expect(sentence.split(/[^a-zäöüß]+/u)).not.toContain(solution);
    });
  });

  test("the field takes the answer, and the reason comes after the check", async () => {
    const [card] = await openPage();
    const field = fieldOf(card);
    // nothing is revealed while the field is empty
    expect(card.querySelector(".choice-explanation")).toBeNull();
    expect(card.querySelector(".steps")).toBeNull();

    typeAndCheck(card, BATCH[0].answer.payload.correct[0]);
    const status = statusOf(card);
    expect(status.classList.contains("good")).toBe(true);
    expect(status.textContent).toContain(strings["ui.completion_correct"]);
    expect(status.textContent).toContain(BATCH[0].answer.payload.explanation[0]);
    expect(field.disabled).toBe(true);
    expect(card.querySelector(".steps")).not.toBeNull();
  });

  test("Enter in the field checks, as the button does", async () => {
    const cards = await openPage();
    // the batch alternates the two formats, so the second card is not a field: the card is
    // found by what it is, not by where it sits
    const card = cards.filter((entry) => fieldOf(entry))[1];
    const index = cards.indexOf(card);
    typeAndCheck(card, BATCH[index].answer.payload.correct[0], { enter: true });
    expect(statusOf(card).textContent).toContain(strings["ui.completion_correct"]);
    // and the button is a submit button inside the form: that is what makes Enter work
    expect(checkOf(cards[0]).getAttribute("type")).toBe("submit");
    expect(fieldOf(cards[0]).closest("form")).not.toBeNull();
  });

  test("a wrong answer says what the right one was, and why", async () => {
    const [card] = await openPage();
    typeAndCheck(card, "falsch");
    const status = statusOf(card);
    expect(status.classList.contains("bad")).toBe(true);
    expect(status.textContent).toContain(strings["ui.completion_wrong"]);
    expect(status.textContent).toContain(BATCH[0].answer.payload.correct[0]);
    expect(status.textContent).toContain(BATCH[0].answer.payload.explanation[0]);
  });

  test("an empty field asks for the word instead of grading nothing", async () => {
    const [card] = await openPage();
    typeAndCheck(card, "   ");
    const status = statusOf(card);
    expect(status.classList.contains("bad")).toBe(true);
    expect(status.textContent).toContain(strings["ui.completion_empty"]);
    expect(fieldOf(card).disabled).toBe(false);
  });

  test("the answer is read forgivingly: case, spaces and the ss which replaces ß", async () => {
    const [card] = await openPage();
    const first = BATCH[0].answer.payload;
    expect(first.accept).toContain("heisse");
    typeAndCheck(card, "  HEISSE. ");
    expect(statusOf(card).textContent).toContain(strings["ui.completion_correct"]);
  });

  test("Riprova gives the card back, empty and unlocked", async () => {
    const [card] = await openPage();
    typeAndCheck(card, "falsch");
    retryOf(card).click();
    expect(fieldOf(card).disabled).toBe(false);
    expect(fieldOf(card).value).toBe("");
    expect(statusOf(card).textContent).toBe("");
    expect(checkOf(card).hidden).toBe(false);
  });

  test("a multiple choice card of the same page is the choice the site already had", async () => {
    const cards = await openPage();
    const card = choiceCard(cards);
    const index = cards.indexOf(card);
    const payload = BATCH[index].answer.payload;
    const options = [...card.querySelectorAll(".choice-option")];
    expect(options).toHaveLength(4);
    expect(options.map((b) => b.querySelector(".choice-text").textContent))
      .toEqual(payload.options);

    const right = options.find((b) => b.querySelector(".choice-text").textContent === payload.correct[0]);
    right.click();
    [...card.querySelectorAll("button")].find((b) => b.textContent === strings["ui.check_answer"]).click();
    const status = statusOf(card);
    expect(status.textContent).toContain(strings["ui.correct"]);
    expect(status.textContent).toContain(payload.explanation[0]);
  });
});

describe("the numbers page", () => {
  test("keeps the umlauts and the ss through the whole chain", async () => {
    const page = findPage("tedesco-zahlen");
    await goTo(`#/${page.macro}/${page.sub}/${page.id}`);
    await vi.waitFor(() => expect(view().querySelectorAll("article.card")).toHaveLength(18));
    const text = view().textContent;
    expect(text).toContain("sechzehn");
    expect(text).toContain("siebzehn");
    expect(text).toContain("30 = ______");
    expect(text).toContain("dreißig");
  });
});

// ---------------------------------------------------------------- what a phone sees
// The operator's report of 2026-11-18: on a 360 px phone he saw only the completion
// cards, and the solution was already printed under the question. What is measured here
// is what can be measured from this box: the DOM the client builds (jsdom has no layout
// engine, so "visible" has to mean "in the document, and not hidden by a rule that holds
// at that width"), and the stylesheet itself — which rule could hide a card's options.

// jsdom rewrites `import.meta.url` to a http:// address, so the sheet is read by path:
// the suite always runs from the web/ directory (vitest's root)
const SHEET = readFileSync(`${process.cwd()}/src/styles.css`, "utf8");

/** Every @media block in the sheet, with its condition and its body. */
function mediaBlocks() {
  const blocks = [];
  const opening = /@media([^{]+)\{/g;
  let match;
  while ((match = opening.exec(SHEET)) !== null) {
    let depth = 1;
    let at = opening.lastIndex;
    while (depth > 0 && at < SHEET.length) {
      if (SHEET[at] === "{") depth += 1;
      else if (SHEET[at] === "}") depth -= 1;
      at += 1;
    }
    blocks.push({ condition: match[1].trim(), body: SHEET.slice(opening.lastIndex, at - 1) });
  }
  return blocks;
}

/** Does this media condition hold on a viewport `width` px wide? Only width is judged. */
function holdsAt(condition, width) {
  const rem = 16;
  const maxPx = [...condition.matchAll(/(?:max-)?width\s*<=?\s*([\d.]+)rem|max-width\s*:\s*([\d.]+)rem/g)]
    .map((m) => Number(m[1] ?? m[2]) * rem);
  if (maxPx.length) return width <= Math.min(...maxPx);
  const minPx = [...condition.matchAll(/min-width\s*:\s*([\d.]+)rem/g)].map((m) => Number(m[1]) * rem);
  if (minPx.length) return width >= Math.max(...minPx);
  return false;               // print, prefers-reduced-motion, and anything that is not width
}

describe("the German page on a phone, at 360 px", () => {
  test("both formats are on the first screen, not after nine cards of one kind", async () => {
    const cards = await openPage();
    const formats = cards.map((card) => (fieldOf(card) ? "completion" : "choice"));
    // 360 px holds one card at a time: the first three are the first screens, and both
    // ways of answering must be among them — the old order put the first choice tenth
    expect(formats.slice(0, 3)).toContain("completion");
    expect(formats.slice(0, 3)).toContain("choice");
  });

  test("no rule that holds at 360 px hides the options, the field or the card", async () => {
    const blocks = mediaBlocks();
    // the phone rule is the one the operator's hypothesis pointed at; it must exist and it
    // must compact, not hide
    const phone = blocks.filter((block) => holdsAt(block.condition, 360));
    expect(phone.length).toBeGreaterThan(0);
    const watched = [".choice-list", ".choice-option", ".completion-form",
      ".completion-input", ".card"];
    for (const block of phone) {
      expect(block.body).not.toMatch(/display\s*:\s*none/);
      expect(block.body).not.toMatch(/visibility\s*:\s*hidden/);
      // and no rule of that block hides one of the card's controls: the phone rule
      // compacts (padding, gap, font size), it does not remove anything
      for (const rule of block.body.split("}")) {
        const [selectors, declarations] = rule.split("{");
        if (!selectors || !declarations) continue;
        const named = watched.some((selector) => selectors.includes(selector));
        if (!named) continue;
        expect(declarations).not.toMatch(/display\s*:\s*none|visibility\s*:\s*hidden/);
      }
    }
    // and the same block does not hold on a desktop viewport: 1280 px is untouched by it
    const desk = blocks.filter((block) => holdsAt(block.condition, 1280));
    expect(desk).toHaveLength(0);
  });

  test("the two counts are the same at 360 px and at 1280 px", async () => {
    const cards = await openPage();
    const completions = cards.filter((card) => fieldOf(card)).length;
    const choices = cards.filter((card) => !fieldOf(card)).length;
    // the numbers the operator asked for: nine and nine, at both widths — the DOM does not
    // depend on the viewport, and the sheet (asserted above) hides neither
    expect([cards.length, completions, choices]).toEqual([18, 9, 9]);
    expect(view().querySelectorAll(".choice-option")).toHaveLength(36);
  });
});

describe("the solution is behind the answer, not beside the question", () => {
  test("no card says which option is right, and none carries the reason, before the answer", async () => {
    const cards = await openPage();
    for (const card of cards) {
      expect(card.querySelector(".choice-correct")).toBeNull();
      expect(card.querySelector(".choice-explanation")).toBeNull();
      // the clue and the rule are the reason: on the German cards the rule names the answer
      expect(card.querySelector("details.steps")).toBeNull();
    }
    // and a completion's solution is nowhere in the card's own text
    cards.filter((card) => fieldOf(card)).forEach((card) => {
      const index = cards.indexOf(card);
      const solution = BATCH[index].answer.payload.correct[0].toLowerCase();
      const words = card.textContent.toLowerCase().split(/[^a-zäöüß]+/u);
      expect(words).not.toContain(solution);
    });
  });

  test("«Mostra la soluzione» is the way out, and it brings the reason with it", async () => {
    const cards = await openPage();
    const card = choiceCard(cards);
    const index = cards.indexOf(card);
    const payload = BATCH[index].answer.payload;
    const reveal = [...card.querySelectorAll("button")]
      .find((button) => button.textContent === strings["ui.reveal"]);
    expect(reveal).toBeTruthy();

    reveal.click();
    const status = statusOf(card);
    expect(status.textContent).toContain(
      strings["ui.solution_is"].replace("{answer}", payload.correct[0]));
    expect(status.textContent).toContain(payload.explanation[0]);
    const right = [...card.querySelectorAll(".choice-option")]
      .find((option) => option.querySelector(".choice-text").textContent === payload.correct[0]);
    expect(right.classList.contains("choice-correct")).toBe(true);
    expect(card.querySelector("details.steps")).not.toBeNull();
    // the check is gone: a revealed card is not an answered one
    expect([...card.querySelectorAll("button")]
      .find((button) => button.textContent === strings["ui.check_answer"]).style.display)
      .toBe("none");
  });

  test("the reason of a correct choice arrives with the check, and Riprova puts it away", async () => {
    const cards = await openPage();
    const card = choiceCard(cards);
    const index = cards.indexOf(card);
    const payload = BATCH[index].answer.payload;
    [...card.querySelectorAll(".choice-option")]
      .find((option) => option.querySelector(".choice-text").textContent === payload.correct[0])
      .click();
    [...card.querySelectorAll("button")]
      .find((button) => button.textContent === strings["ui.check_answer"]).click();
    expect(statusOf(card).textContent).toContain(payload.explanation[0]);
    expect(card.querySelector("details.steps")).not.toBeNull();

    [...card.querySelectorAll("button")]
      .find((button) => button.textContent === strings["ui.try_again"]).click();
    // the rule went with the answer: a retry must not be a reading exercise
    expect(card.querySelector("details.steps")).toBeNull();
    expect(card.querySelector(".choice-explanation")).toBeNull();
  });
});
