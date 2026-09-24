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
    board.create("point", [x, y], {
      size: 7,
      face: "circle",
      fillColor: tokens.danger,
      strokeColor: "#fff",
      strokeWidth: 3,
      fixed: true,
      name: label(strings, marker.label_key, marker.label_key),
      withLabel: true,
      label: { position: "rt", offset: [12, 14], fontSize: GRAPH_FONT },
    });
  });

  board.update();
  return board;
}
