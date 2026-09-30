// Figure JSON -> JSXGraph. The browser only draws what the server decided.
import JXG from "../vendor/jsxgraphcore.js";
import "../vendor/jsxgraph.css";

// A kinematics plot has seconds on x and metres on y: the two axes must NOT keep a
// shared pixel aspect ratio, or JSXGraph widens one range to preserve the ratio and
// the plotted line lands outside the visible box (observed: an empty grid).
const PAD = 0.08;

// Graph text must be legible on a classroom projector and in a printed worksheet: the
// JSXGraph defaults (12 px) are too small on the axis ticks, which is where the student
// actually reads the numbers. The values live in the stylesheet (styles.css §1), so the
// whole site's graphs are resized from one place.
function cssToken(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

function graphTokens() {
  return {
    font: parseFloat(cssToken("--graph-font", "20")) || 20,
    axisFont: parseFloat(cssToken("--graph-axis-font", "22")) || 22,
    danger: cssToken("--danger", "#c0392b"),
    guide: cssToken("--guide", "#8b949e"),
    // one colour per motion-segment kind, matching the legend the page draws
    kinds: {
      uniform: cssToken("--kind-uniform", "#1f6feb"),
      accelerate: cssToken("--kind-accelerate", "#1a7f37"),
      decelerate: cssToken("--kind-decelerate", "#bf8700"),
    },
  };
}

/**
 * A drawing coordinate -> number.
 *
 * The wire carries exact rationals ("-7/2", "3"), which `Number()` reads as `NaN`: that is
 * how every trace of a graph once collapsed to nothing while the legend still listed it.
 * Only here, at the boundary, is the exact value turned into a float — the payload keeps
 * the exact form, and the server verifies against it.
 */
function toNumber(value) {
  if (typeof value === "number") return value;
  const text = String(value).trim();
  const rational = /^(-?\d+)\/(\d+)$/.exec(text);
  if (rational) return Number(rational[1]) / Number(rational[2]);
  return Number(text);
}

function extent(values) {
  const nums = values.map(toNumber).filter((n) => Number.isFinite(n));
  if (!nums.length) return [0, 1];
  return [Math.min(...nums), Math.max(...nums)];
}

function label(strings, key, fallback) {
  return strings?.[key] ?? fallback ?? key;
}

/**
 * Tick numbers and axis names are drawn OUTSIDE the axes, so they need a margin in PIXELS;
 * the 8 % of the range reserved above is a comfortable inset on a desktop and a handful of
 * pixels on a phone, where the y label "100" ran off the left edge of the plot and read as
 * "00" (measured at 390 px: 14 px cut, plus 4 px under the x tick numbers). Measure where
 * the labels actually landed and grow the viewport by what they need — on a container that
 * has the room already, every measurement is zero and the box is left as computed.
 *
 * A card is built detached and appended only afterwards, so at this point the container has
 * no box and JSXGraph has not drawn its labels yet: wait for the first real layout rather
 * than measuring zeros. (JSXGraph sizes itself from the same resize signal.)
 */
function reserveLabelRoom(board, container) {
  if (measureLabelRoom(board, container)) return;
  // A card is built detached and only then appended, and JSXGraph draws its SVG off a
  // resize signal of its own: until both have happened there is nothing to measure. Watch
  // for either event; the observers go away the moment a measurement succeeds.
  const cancel = [];
  const attempt = () => {
    if (!measureLabelRoom(board, container)) return;
    cancel.forEach((stop) => stop());
  };
  if (typeof ResizeObserver === "function") {
    const observer = new ResizeObserver(attempt);
    observer.observe(container);
    cancel.push(() => observer.disconnect());
  }
  if (typeof MutationObserver === "function") {
    const observer = new MutationObserver(attempt);
    observer.observe(container, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["width", "height", "style"],
    });
    cancel.push(() => observer.disconnect());
  }
}

/** @returns {boolean} true once a laid-out plot with rendered labels has been measured */
function measureLabelRoom(board, container) {
  const frame = container.getBoundingClientRect();
  const svg = container.querySelector("svg");
  if (!frame.width || !frame.height || !svg || !svg.getBoundingClientRect().width) return false;
  for (let pass = 0; pass < 2; pass += 1) {
    const need = { left: 0, top: 0, right: 0, bottom: 0 };
    container.querySelectorAll("text").forEach((text) => {
      const rect = text.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      need.left = Math.max(need.left, frame.left - rect.left);
      need.top = Math.max(need.top, frame.top - rect.top);
      need.right = Math.max(need.right, rect.right - frame.right);
      need.bottom = Math.max(need.bottom, rect.bottom - frame.bottom);
    });
    if (!(need.left > 0 || need.top > 0 || need.right > 0 || need.bottom > 0)) return true;
    const [left, top, right, bottom] = board.getBoundingBox();
    const slack = 2;                       // the glyph box is tight around the digits
    const scaleX = (right - left) / frame.width;
    const scaleY = (bottom - top) / frame.height;
    board.setBoundingBox([
      left - (need.left + slack) * scaleX,
      top + (need.top + slack) * scaleY,
      right + (need.right + slack) * scaleX,
      bottom - (need.bottom + slack) * scaleY,
    ], false);
    board.update();
  }
  return true;
}

export function renderFigure(container, figure, strings) {
  if (!figure) return null;              // algebra items have no figure
  const tokens = graphTokens();
  const GRAPH_FONT = tokens.font;
  const AXIS_FONT = tokens.axisFont;
  // Set once per render: tick labels, axis names and every element label inherit this.
  JXG.Options.text.fontSize = GRAPH_FONT;
  JXG.Options.text.highlightStrokeWidth = 1;
  JXG.Options.label.fontSize = GRAPH_FONT;
  const traces = figure.traces ?? [];
  const markers = figure.markers ?? [];
  // An empty graph (graph_filling pages) still needs axes, so only a missing figure
  // stops us here.

  const xs = traces.flatMap((t) => t.samples.map(([x]) => x)).concat(markers.map((m) => m.at[0]));
  const ys = traces.flatMap((t) => t.samples.map(([, y]) => y)).concat(markers.map((m) => m.at[1]));

  // Name the y axis after the quantity it carries ("s(t) [m]"), not only its unit.
  const quantityKey = figure.y_label ?? traces[0]?.label_key;
  const quantity = quantityKey ? label(strings, quantityKey, quantityKey) : null;
  const domain = figure.domain ?? { t_min: "0", t_max: "1" };
  let [xMin, xMax] = extent(xs.length ? xs : [domain.t_min ?? "0", domain.t_max ?? "1"]);
  // A hidden figure carries the intended y scale so the student's grid is meaningful.
  let [yMin, yMax] = extent(ys.length ? ys : figure.y_range ?? ["0", "1"]);
  // "corner" figures start at zero: no negative time, so the axes meet in the bottom-left.
  // The padding stays on EVERY side, because JSXGraph draws tick numbers *outside* the
  // axes: with the viewport ending exactly at zero they are clipped away and the graph
  // loses its scale (observed live: an empty-looking plot with a correct legend).
  const corner = figure.origin === "corner";
  xMin = corner ? 0 : Math.min(0, xMin);
  yMin = corner ? 0 : Math.min(0, yMin);
  const padX = (xMax - xMin || 1) * PAD;
  const padY = (yMax - yMin || 1) * PAD;

  const board = JXG.JSXGraph.initBoard(container, {
    // [left, top, right, bottom] in data units
    // [left, top, right, bottom]: the small margin is what the tick numbers are drawn in
    boundingbox: [xMin - padX, yMax + padY, xMax + padX, yMin - padY],
    keepaspectratio: false,
    axis: true,
    showNavigation: false,
    showCopyright: false,
    pan: { enabled: false },
    zoom: { enabled: false },
    defaultAxes: {
      x: {
        name: `t [${figure.x_unit}]`,
        withLabel: true,
        label: { position: "rt", offset: [-46, 26], fontSize: AXIS_FONT },
        ticks: { label: { fontSize: GRAPH_FONT }, strokeColor: "#57606a" },
      },
      y: {
        name: `${quantity ? `${quantity} ` : ""}[${figure.y_unit}]`,
        withLabel: true,
        label: { position: "rt", offset: [14, -12], fontSize: AXIS_FONT },
        ticks: { label: { fontSize: GRAPH_FONT }, strokeColor: "#57606a" },
      },
    },
  });

  // The traces are drawn as explicit straight segments between consecutive samples, not as
  // a JSXGraph `curve`: with a handful of coordinates at the ends of its sampling range the
  // curve emits a path of `M` commands only — a path that strokes nothing — which is how a
  // graph came out empty next to a correct legend. Segments always draw.
  const labelTraces = traces.length > 1;
  const palette = [tokens.kinds.uniform, "#d29922", "#8250df", tokens.kinds.accelerate];
  traces.forEach((trace, index) => {
    const points = trace.samples.map(([x, y]) => [toNumber(x), toNumber(y)]);
    // A coordinate the browser cannot read is a broken payload, not an empty graph: say so
    // in the console instead of drawing nothing (observed: Number("21/4") is NaN, and the
    // whole trace silently vanished while the legend still listed it).
    const unreadable = trace.samples.filter(([x, y]) => !Number.isFinite(toNumber(x)) || !Number.isFinite(toNumber(y)));
    if (unreadable.length) {
      console.error(`figure: unreadable coordinates in trace "${trace.kind ?? index}"`, unreadable.slice(0, 3));
      return;
    }
    const stroke = tokens.kinds[trace.kind] ?? palette[index % palette.length];
    for (let i = 1; i < points.length; i += 1) {
      board.create("segment", [points[i - 1], points[i]], {
        strokeColor: stroke,
        strokeWidth: 4,
        fixed: true,
        highlight: false,
        // the legend names every segment, so only a two-trace plot labels its lines
        name: labelTraces && traces.length <= 2 ? label(strings, trace.label_key, trace.label_key) : "",
        withLabel: false,
      });
    }
  });

  // the vertices of the broken line: white-centred dots ringed in the segment's colour,
  // large enough to read from the back of a classroom
  (figure.vertices ?? []).forEach((vertex) => {
    const [x, y] = vertex.at.map(toNumber);
    board.create("point", [x, y], {
      size: 6,
      face: "circle",
      // filled, with a white ring: a hollow dot reads as a break in the line
      fillColor: tokens.kinds[vertex.kind] ?? "#1f6feb",
      strokeColor: "#fff",
      strokeWidth: 2,
      fixed: true,
      highlight: false,
      withLabel: false,
    });
  });

  // dashed dividers between motion segments
  (figure.guides ?? []).forEach((guide) => {
    const x = toNumber(guide.at);
    board.create("segment", [[x, yMin], [x, yMax]], {
      strokeColor: tokens.guide,
      strokeWidth: 2,
      dash: 2,
      fixed: true,
    });
  });

  markers.forEach((marker) => {
    const [x, y] = marker.at.map(toNumber);
    // The label sits beside its own dot, on the side that still has plot left: anchored to
    // the right, a marker near the end of the domain pushed its label outside the box and
    // the board clipped it (observed: "istante richiesto" cut to "richie").
    const atRight = x > (xMin + xMax) / 2;
    board.create("point", [x, y], {
      size: 7,
      face: "circle",
      fillColor: tokens.danger,
      strokeColor: "#fff",
      strokeWidth: 3,
      fixed: true,
      name: label(strings, marker.label_key, marker.label_key),
      withLabel: true,
      // clear of its own dot: the label used to touch the marker it names
      label: {
        position: atRight ? "lt" : "rt",
        offset: atRight ? [-12, 30] : [20, 30],
        fontSize: GRAPH_FONT,
      },
    });
  });

  board.update();
  reserveLabelRoom(board, container);
  return board;
}
