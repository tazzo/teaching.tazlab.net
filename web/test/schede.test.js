// The sheets section, driven end to end in jsdom: the menu entry, the page it opens, and
// the row that tells the operator which version his saved link is giving him today.
//
// The list is the server's (`web/test/fixtures/schede.json`, pinned against /api/schede by
// `tests/test_web_fixture.py`): a recompiled sheet moves the sha256 and the version, and
// the pin makes that visible instead of letting this suite certify a PDF nobody serves.
//
// What is asserted is what the operator would check by hand: the menu has the section, one
// click lands on the sheets without a topic level in between, the link is the stable
// address, and under it there are the date, the commit and the full sha256.

import { afterEach, beforeAll, beforeEach, describe, expect, test, vi } from "vitest";

import catalogue from "./fixtures/pages.json";
import sheets from "./fixtures/schede.json";
import strings from "../../app/i18n/it.json";

const { main } = await import("../src/app.js");

const view = () => document.getElementById("view");
const requested = [];

const ok = (body) => ({ ok: true, status: 200, json: async () => body });

function stubFetch(override = {}) {
  return vi.fn(async (url) => {
    const path = String(url);
    requested.push(path);
    const replaced = Object.entries(override).find(([prefix]) => path.startsWith(prefix));
    if (replaced) return replaced[1];
    if (path.startsWith("/api/i18n")) return ok(strings);
    if (path.startsWith("/api/pages")) return ok(catalogue);
    if (path.startsWith("/api/schede")) return ok(sheets);
    throw new Error(`unexpected request: ${path}`);
  });
}

const goTo = async (hash) => {
  history.replaceState(null, "", location.pathname);
  location.hash = hash;
  await new Promise((resolve) => setTimeout(resolve, 0));
  window.dispatchEvent(new HashChangeEvent("hashchange"));
  await Promise.resolve();
};

const SHEET = sheets.schede[0];

let booted = [];
beforeAll(async () => {
  document.body.innerHTML = '<h1 id="title"><a href="#/">Didattica</a></h1>' +
    '<nav id="topnav"></nav><main id="view"></main>';
  window.scrollTo = () => {};
  vi.stubGlobal("fetch", stubFetch());
  await main();
  booted = [...requested];
});

beforeEach(async () => {
  vi.stubGlobal("fetch", stubFetch());
  await goTo("#/");
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const openSheets = async () => {
  await goTo("#/schede");
  await vi.waitFor(() => expect(view().querySelectorAll(".scheda")).toHaveLength(sheets.schede.length));
  return [...view().querySelectorAll(".scheda")];
};

describe("the sheets section", () => {
  test("is in the menu, labelled from the catalogue", () => {
    expect(catalogue.macros).toContain("schede");
    const labels = [...document.querySelectorAll("#topnav a")].map((a) => a.textContent);
    expect(labels).toContain(strings["macro.schede"]);
    const link = [...document.querySelectorAll("#topnav a")]
      .find((a) => a.getAttribute("href") === "#/schede");
    expect(link).not.toBeUndefined();
  });

  test("one click lands on the page: the section holds a single page, so there is no index in between", async () => {
    await openSheets();
    // the sheets, not a list of sub-topics
    expect(view().querySelectorAll(".link-list")).toHaveLength(0);
    expect(view().querySelector("h2").textContent).toBe(strings["page.schede.matematica"]);
    expect(view().querySelector(".page-intro").textContent).toBe(strings["intro.schede"]);
    expect(requested).toContain("/api/schede");
  });

  test("every sheet is a row with its title, its subtitle and a stable link", async () => {
    const rows = await openSheets();
    sheets.schede.forEach((sheet, index) => {
      const row = rows[index];
      expect(row.querySelector(".scheda-title").textContent).toBe(sheet.title);
      expect(row.querySelector(".scheda-subtitle").textContent).toBe(sheet.subtitle);
      const link = row.querySelector("a.btn");
      expect(link.getAttribute("href")).toBe(sheet.url);
      // the stable name is the one on the server, and it carries no date
      expect(sheet.url).toBe(`/schede/${sheet.file}`);
      expect(sheet.file).not.toMatch(/20\d{2}/);
      // the download keeps the sheet's own name, which a teacher recognises
      expect(link.getAttribute("download")).toBe(sheet.file.split("/").pop());
      expect(link.textContent).toBe(strings["ui.schede_open"]);
    });
  });

  test("the page says which version, with the date and the commit", async () => {
    const [row] = await openSheets();
    expect(SHEET.updated).toBeTruthy();
    expect(SHEET.commit).toBeTruthy();
    const version = row.querySelector(".scheda-version").textContent;
    expect(version).toBe(
      strings["ui.schede_updated"]
        .replace("{date}", SHEET.updated)
        .replace("{commit}", SHEET.commit),
    );
    // the sentence a reader would check against the PDF
    expect(version).toContain(SHEET.updated);
    expect(version).toContain(SHEET.commit);
  });

  test("the page prints the whole sha256, so the download can be checked against it", async () => {
    const [row] = await openSheets();
    expect(row.querySelector(".scheda-hash-label").textContent).toBe(strings["ui.schede_sha"]);
    const digest = row.querySelector(".scheda-hash code").textContent;
    expect(digest).toBe(SHEET.sha256);
    expect(digest).toMatch(/^[0-9a-f]{64}$/);
    expect(row.querySelector(".scheda-hint").textContent).toBe(strings["ui.schede_verify"]);
  });

  test("the size is shown and says nothing false", async () => {
    const [row] = await openSheets();
    const size = row.querySelector(".scheda-size").textContent;
    expect(size).toBe(`${Math.max(1, Math.round(SHEET.bytes / 1024))} kB`);
  });

  test("a sheet with a date but no commit says 'compilata il', it does not invent an author", async () => {
    const noCommit = {
      schede: [{ ...SHEET, commit: null, versionSource: "pdf" }],
    };
    vi.stubGlobal("fetch", stubFetch({
      "/api/schede": ok(noCommit),
    }));
    const [row] = await openSheets();
    expect(row.querySelector(".scheda-version").textContent)
      .toBe(strings["ui.schede_compiled"].replace("{date}", SHEET.updated));
  });

  test("a section with more than one page keeps its index", async () => {
    // the rule that opens a single-page section must not swallow the ordinary ones
    await goTo("#/tedesco");
    expect(view().querySelectorAll(".link-list li").length)
      .toBe(catalogue.subs.tedesco.length);
  });

  test("an empty list says so instead of drawing nothing", async () => {
    vi.stubGlobal("fetch", stubFetch({ "/api/schede": ok({ schede: [] }) }));
    await goTo("#/schede");
    await vi.waitFor(() => expect(view().querySelector(".status").textContent)
      .toBe(strings["ui.schede_empty"]));
  });

  test("the boot asked only for what the shell needs", () => {
    expect(booted.slice(0, 2)).toEqual(["/api/i18n", "/api/pages"]);
  });
});
