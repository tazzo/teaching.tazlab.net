// Configurator — rendered from the control descriptor the topic declares (STRUCTURE §4.2).
//
// The page does not know what a "segment" is: it iterates the descriptor served by
// /api/pages and builds one field per control. Two control kinds exist today; an unknown
// kind is skipped with a warning rather than breaking the page.

import { el } from "./pages.js";

function field(labelText, control, hint) {
  const label = el("label", "config-field");
  label.append(el("span", "config-label", labelText));
  label.append(control);
  if (hint) label.append(el("span", "hint", hint));
  return label;
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

/**
 * One selector per segment, as many as the control the descriptor points at says — the
 * operator picks 3, 4 or 5 segments and each row's motion is drawn at random unless it
 * is pinned here. Changing the count rebuilds the rows and keeps the pinned ones.
 */
function segmentKinds(control, t, defaults, countSelect) {
  const wrap = el("div", "config-segments");
  const rows = el("div", "config-rows");
  const pinned = Array.isArray(defaults) ? [...defaults] : [];
  const randomValue = control.choices[0].value;

  const build = () => {
    const wanted = Math.max(1, Number(countSelect?.value) || 1);
    rows.replaceChildren();
    for (let index = 0; index < wanted; index += 1) {
      const row = el("div", "config-row");
      row.append(el("span", "config-row-index", String(index + 1)));
      row.append(selectFrom(control.choices, t, pinned[index] ?? randomValue));
      rows.append(row);
    }
  };

  countSelect?.addEventListener("change", build);
  build();
  wrap.append(rows);
  const read = () => [...rows.querySelectorAll("select")].map((select) => select.value);
  return { node: wrap, read };
}

/**
 * Build the whole configurator.
 * @returns {{node: HTMLElement, read: () => object}}
 */
export function renderConfigurator(descriptor, defaults = {}, strings) {
  const t = (key, fallback) => strings?.[key] ?? fallback ?? key;
  const form = el("form", "configurator");
  form.onsubmit = (event) => event.preventDefault();
  const readers = [];
  const nodes = {};

  // The plain selectors are built first: a row list names the control that drives its
  // length, and that must not depend on the order the descriptor happens to be written in.
  (descriptor ?? []).filter((control) => control.kind === "select")
    .forEach((control) => {
      nodes[control.id] = selectFrom(control.choices, t, defaults[control.id]);
    });

  (descriptor ?? []).forEach((control) => {
    const hint = control.hint_key ? t(control.hint_key) : null;
    if (control.kind === "select") {
      form.append(field(t(control.label_key, control.id), nodes[control.id], hint));
      readers.push(() => ({ [control.id]: nodes[control.id].value }));
    } else if (control.kind === "segment_kinds") {
      const list = segmentKinds(control, t, defaults[control.id], nodes[control.count_from]);
      form.append(field(t(control.label_key, control.id), list.node, hint));
      readers.push(() => ({ [control.id]: list.read() }));
    } else {
      console.warn(`configurator: unknown control kind "${control.kind}" (${control.id})`);
    }
  });

  const read = () => Object.assign({}, ...readers.map((reader) => reader()));
  return { node: form, read };
}