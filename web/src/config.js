// Configurator — rendered from the control descriptor the topic declares (STRUCTURE §4.2).
//
// The page does not know what a "segment" is: it iterates the descriptor served by
// /api/pages and builds one field per control. A new configurable page therefore needs
// only a `configurer()` on its topic — no client code. Two control kinds exist today;
// an unknown kind is skipped with a warning rather than breaking the page.

import { el } from "./pages.js";

function field(labelText, control, hint, tag = "label") {
  const wrapper = el(tag, "config-field");
  wrapper.append(el("span", "config-label", labelText));
  wrapper.append(control);
  if (hint) wrapper.append(el("span", "hint", hint));
  return wrapper;
}

function selectFrom(choices, t, selected) {
  const select = el("select", "config-select");
  choices.forEach((choice) => {
    const option = el("option", null, t(choice.label_key, choice.value));
    option.value = choice.value;
    select.append(option);
  });
  if (selected) select.value = selected;
  return select;
}

/** A list of N segment selectors with add/remove — the motion's structure. */
function segmentList(control, t, defaults) {
  const wrap = el("div", "config-segments");
  const rows = el("div", "config-rows");
  const initial = Array.isArray(defaults) && defaults.length ? defaults : [control.choices[0].value];

  const addRow = (value) => {
    const row = el("div", "config-row");
    row.append(el("span", "config-row-index", String(rows.children.length + 1)));
    row.append(selectFrom(control.choices, t, value));
    const remove = el("button", "btn btn-icon config-remove", "\u00d7");
    remove.type = "button";
    remove.title = t("config.remove_segment");
    remove.addEventListener("click", () => {
      if (rows.children.length > (control.min ?? 1)) row.remove();
      renumber();
    });
    row.append(remove);
    rows.append(row);
  };
  const renumber = () => {
    [...rows.children].forEach((row, index) => {
      row.querySelector(".config-row-index").textContent = String(index + 1);
    });
    syncButtons();
  };
  const syncButtons = () => {
    const full = rows.children.length >= (control.max ?? 4);
    add.disabled = full;
    [...rows.querySelectorAll(".config-remove")].forEach((button) => {
      button.disabled = rows.children.length <= (control.min ?? 1);
    });
  };

  initial.forEach(addRow);
  const add = el("button", "btn btn-quiet config-add", `+ ${t("config.add_segment")}`);
  add.type = "button";
  add.addEventListener("click", () => {
    // a new segment continues the motion in the most teachable way: uniform
    addRow(control.choices[0].value);
    renumber();
  });
  wrap.append(rows, add);
  const read = () => [...rows.querySelectorAll("select")].map((select) => select.value);
  renumber();
  return { node: wrap, read };
}

/**
 * Build the whole configurator.
 * @returns {{node: HTMLElement, read: () => object, summary: () => string}}
 */
export function renderConfigurator(descriptor, defaults = {}, strings) {
  const t = (key, fallback) => strings?.[key] ?? fallback ?? key;
  // A div, not a form: the configurator is appended inside the page's own form, and a
  // form nested in a form is not valid markup — the outer form already owns submission.
  const group = el("div", "configurator");
  const readers = [];

  (descriptor ?? []).forEach((control) => {
    const hint = control.hint_key ? t(control.hint_key) : null;
    if (control.kind === "select") {
      const select = selectFrom(control.choices, t, defaults[control.id]);
      group.append(field(t(control.label_key, control.id), select, hint));
      readers.push(() => ({ [control.id]: select.value }));
    } else if (control.kind === "segment_list") {
      const list = segmentList(control, t, defaults[control.id]);
      // its own block, not a label: a button inside a label would activate the select
      const block = field(t(control.label_key, control.id), list.node, hint, "div");
      // the structure of the motion is the main choice and carries a hint: give it room
      block.classList.add("config-field-wide");
      group.append(block);
      readers.push(() => ({ [control.id]: list.read() }));
    } else {
      console.warn(`configurator: unknown control kind "${control.kind}" (${control.id})`);
    }
  });

  const read = () => Object.assign({}, ...readers.map((reader) => reader()));
  return { node: group, read };
}
