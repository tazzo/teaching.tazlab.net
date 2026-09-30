// The configurator renders from the descriptor the server serves — the descriptor in
// `fixtures/pages.json` is that response, byte for byte, and `tests/test_web_fixture.py`
// fails if the two drift apart. So every control below is a control a classroom gets.
//
// What is asserted, and no more: one field per control, one selector per segment as the
// count field says, the served defaults preselected, and a `read()` the generator
// accepts. No DOM snapshot: a snapshot would pass just as happily on the wrong
// resolution of a merge conflict, which is the failure this gate exists for (TD-110).

import { afterEach, describe, expect, test, vi } from "vitest";

import { renderConfigurator } from "../src/config.js";
import catalogue from "./fixtures/pages.json";
// the same table GET /api/i18n serves, imported from the file the server reads
import strings from "../../app/i18n/it.json";

const page = catalogue.pages.find((entry) => entry.config.length > 0);
const descriptor = page.config;
const controls = Object.fromEntries(descriptor.map((control) => [control.id, control]));
const selectControls = descriptor.filter((control) => control.kind === "select");
const segmentControls = descriptor.filter((control) => control.kind === "segment_kinds");

afterEach(() => {
  document.body.replaceChildren();
});

const build = (defaults = page.defaults) => {
  const configurator = renderConfigurator(descriptor, defaults, strings);
  document.body.append(configurator.node);
  return configurator;
};

/** The `<select>` belonging to a plain control, found through its own field. */
const fieldOf = (node, id) =>
  [...node.querySelectorAll(".config-field")].find(
    (field) => field.querySelector(".config-label")?.textContent === strings[controls[id].label_key],
  );

const selectOf = (node, id) => fieldOf(node, id).querySelector("select");
const rowSelects = (node) => [...node.querySelectorAll(".config-rows select")];

describe("the configurator served by /api/pages", () => {
  test("the fixture carries the controls the suite assumes", () => {
    // if the catalogue ever stops serving a configurator, the rest of this file would
    // quietly pass on an empty descriptor — say so instead
    expect(selectControls.length).toBeGreaterThan(0);
    expect(segmentControls.length).toBeGreaterThan(0);
    expect(segmentControls.every((control) => control.count_from)).toBe(true);
  });

  test("one field per select control, one option per choice", () => {
    const { node } = build();
    for (const control of selectControls) {
      const field = fieldOf(node, control.id);
      expect(field, `no field for control "${control.id}"`).toBeTruthy();
      const select = field.querySelector("select");
      // the label is translated text, not the raw key: an untranslated label means the
      // strings table lost the key, and a key shown to a student is a bug, not a fallback
      expect(field.querySelector(".config-label").textContent).not.toBe(control.label_key);
      expect([...select.options].map((option) => option.value))
        .toEqual(control.choices.map((choice) => choice.value));
    }
  });

  test("the served defaults are preselected", () => {
    const { node } = build();
    for (const control of selectControls) {
      expect(selectOf(node, control.id).value, `default for "${control.id}"`)
        .toBe(String(page.defaults[control.id]));
    }
    for (const control of segmentControls) {
      const pinned = page.defaults[control.id] ?? [];
      expect(rowSelects(node).map((select) => select.value))
        .toEqual(pinned.map(String));
    }
  });

  test("a default is honoured even when it is not the first choice", () => {
    // Every control the catalogue serves currently defaults to its own first choice, so
    // the test above passes just as well on a renderer that ignores `defaults` — which is
    // the regression this line exists to catch. Here each default is a *later* choice,
    // so only honouring it can pass.
    const chosen = Object.fromEntries(selectControls.map((control) => [
      control.id,
      control.choices.at(-1).value,          // the last choice, never the first
    ]));
    const { node } = build({ ...page.defaults, ...chosen });
    for (const control of selectControls) {
      expect(selectOf(node, control.id).value, `default for "${control.id}"`)
        .toBe(chosen[control.id]);
      expect(chosen[control.id]).not.toBe(control.choices[0].value);
    }
  });

  test("one selector per segment, as many as count_from says", () => {
    const { node } = build();
    const control = segmentControls[0];
    const driver = selectOf(node, control.count_from);

    for (const choice of controls[control.count_from].choices) {
      driver.value = choice.value;
      driver.dispatchEvent(new Event("change"));
      expect(rowSelects(node), `segments for count=${choice.value}`)
        .toHaveLength(Number(choice.value));
    }
  });

  test("changing the count keeps the segments the defaults pinned", () => {
    const control = segmentControls[0];
    const kinds = controls[control.id].choices.map((choice) => choice.value);
    // a distinct default per row, so "kept" cannot be confused with "reset to random"
    const pinned = kinds.slice(0, Number(page.defaults[control.count_from]));
    const { node, read } = build({ ...page.defaults, [control.id]: pinned });
    const driver = selectOf(node, control.count_from);

    const longer = controls[control.count_from].choices.at(-1).value;
    expect(Number(longer)).toBeGreaterThan(pinned.length);
    driver.value = longer;
    driver.dispatchEvent(new Event("change"));

    const rows = [...rowSelects(node)];
    expect(rows).toHaveLength(Number(longer));
    // the pinned rows come back after the rebuild...
    expect(rows.slice(0, pinned.length).map((select) => select.value)).toEqual(pinned);
    // ...and the new ones fall back to the descriptor's first choice (a random draw),
    // not to undefined: the form must always be submittable
    expect(read()[control.id]).toEqual([...pinned,
      ...Array(Number(longer) - pinned.length).fill(kinds[0])]);
  });

  test("read() returns a payload the generator accepts", () => {
    const { read } = build();
    const values = read();

    // the payload's keys are the control ids and nothing else, and every value is one
    // the descriptor offers: the generator refuses anything else, so a form that invents
    // a value is a 400 waiting for the teacher's first click
    expect(Object.keys(values).sort()).toEqual(descriptor.map((control) => control.id).sort());
    for (const control of selectControls) {
      expect(control.choices.map((choice) => choice.value)).toContain(values[control.id]);
    }
    for (const control of segmentControls) {
      const kinds = values[control.id];
      // one entry per segment, and it agrees with the count field driving the rows:
      // a payload whose two fields contradict each other is refused server-side
      expect(kinds).toHaveLength(Number(values[control.count_from]));
      for (const kind of kinds) {
        expect(control.choices.map((choice) => choice.value)).toContain(kind);
      }
    }
  });

  test("read() follows the operator's choices", () => {
    const { node, read } = build();
    const control = segmentControls[0];
    const driver = selectOf(node, control.count_from);
    const target = controls[control.count_from].choices[1].value;
    driver.value = target;
    driver.dispatchEvent(new Event("change"));
    rowSelects(node)[0].value = controls[control.id].choices[1].value;

    const values = read();
    expect(values[control.count_from]).toBe(target);
    expect(values[control.id][0]).toBe(controls[control.id].choices[1].value);
  });

  test("an unknown control kind is skipped, not rendered as a broken field", () => {
    const unknown = [...descriptor, { id: "future", kind: "colour_picker", choices: [] }];
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const configurator = renderConfigurator(unknown, page.defaults, strings);
    document.body.append(configurator.node);

    expect(configurator.node.querySelectorAll(".config-field")).toHaveLength(descriptor.length);
    expect(configurator.read()).toEqual(build().read());
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("colour_picker"));
  });
});
