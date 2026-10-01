// The box the plot is drawn in, which is where a negative value used to disappear.
//
// The measured quantity on these graphs is signed: a motion running the other way is drawn
// below the time axis, a body at rest on it. The renderer once pinned the bottom of the box
// to zero for a "corner" figure, which drew every such sample *outside* the plot — a page
// that showed an empty grid while the payload, the legend and the ticks were all correct
// (the same class of defect as the exact-rational coordinates: nothing server-side could
// see it, because the payload was right). So the invariant lives here, on the box itself.

import { describe, expect, test } from "vitest";

import { renderFigure } from "../src/figure.js";

const crossing = {
  kind: "kinematics",
  origin: "corner",
  x_unit: "s",
  y_unit: "m/s",
  y_label: "trace.velocity",
  domain: { t_min: "0", t_max: "12" },
  traces: [
    { label_key: "trace.velocity", samples: [["0", "-2"], ["6", "-8"], ["12", "-14"]] },
  ],
  vertices: [],
  markers: [],
  guides: [],
};

const below = {
  ...crossing,
  traces: [
    { label_key: "trace.velocity", samples: [["0", "-1"], ["6", "-3"], ["12", "-5"]] },
  ],
};

// jsdom has no layout engine, so the box a board computes is NaN until the host claims a
// size. These are the two properties JSXGraph measures the container with.
const host = () => {
  const node = document.createElement("div");
  for (const [name, value] of [["clientWidth", 800], ["clientHeight", 400],
                               ["offsetWidth", 800], ["offsetHeight", 400]]) {
    Object.defineProperty(node, name, { value });
  }
  node.getBoundingClientRect = () => ({
    x: 0, y: 0, top: 0, right: 800, bottom: 400, left: 0, width: 800, height: 400,
  });
  document.body.append(node);
  return node;
};

describe("the plot box", () => {
  test("holds every drawn sample, on either side of the axis", () => {
    const [left, top, right, bottom] = renderFigure(host(), crossing, {}).getBoundingBox();
    for (const [x, y] of crossing.traces[0].samples) {
      expect(Number(x)).toBeGreaterThanOrEqual(left);
      expect(Number(x)).toBeLessThanOrEqual(right);
      expect(Number(y)).toBeGreaterThanOrEqual(bottom);
      expect(Number(y)).toBeLessThanOrEqual(top);
    }
  });

  test("keeps the zero line inside, so the sign of the quantity is readable", () => {
    // the whole motion below the axis: the time axis is then the *top* of the plot, and a
    // box that stopped at the highest sample would draw it outside
    const [left, top, right, bottom] = renderFigure(host(), below, {}).getBoundingBox();
    expect(bottom).toBeLessThanOrEqual(-5);
    expect(top).toBeGreaterThanOrEqual(0);
    // and the time axis still starts at zero, with the tick numbers' margin beside it
    expect(left).toBeLessThanOrEqual(0);
    expect(right).toBeGreaterThanOrEqual(12);
  });
});
