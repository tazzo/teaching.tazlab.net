// Figure JSON -> JSXGraph. The browser only draws what the server decided.
import JXG from "../vendor/jsxgraphcore.js";
import "../vendor/jsxgraph.css";

// A kinematics plot has seconds on x and metres on y: the two axes must NOT keep a
// shared pixel aspect ratio, or JSXGraph widens one range to preserve the ratio and
// the plotted line lands outside the visible box (observed: an empty grid).
const PAD = 0.08;

function extent(values) {
  const nums = values.map(Number).filter((n) => Number.isFinite(n));
  if (!nums.length) return [0, 1];
  return [Math.min(...nums), Math.max(...nums)];
}

function label(strings, key, fallback) {
  return strings?.[key] ?? fallback ?? key;
}

export function renderFigure(container, figure, strings) {
  if (!figure) return null;              // algebra items have no figure
  const traces = figure.traces ?? [];
  const markers = figure.markers ?? [];
  if (!traces.length && !markers.length) return null;

  const xs = traces.flatMap((t) => t.samples.map(([x]) => x)).concat(markers.map((m) => m.at[0]));
  const ys = traces.flatMap((t) => t.samples.map(([, y]) => y)).concat(markers.map((m) => m.at[1]));

  let [xMin, xMax] = extent(xs.length ? xs : ["0", "1"]);
  let [yMin, yMax] = extent(ys.length ? ys : ["0", "1"]);
  // always show the origin, so the graph reads as a physical plot
  xMin = Math.min(0, xMin);
  yMin = Math.min(0, yMin);
  const padX = (xMax - xMin || 1) * PAD;
  const padY = (yMax - yMin || 1) * PAD;

  const board = JXG.JSXGraph.initBoard(container, {
    // [left, top, right, bottom] in data units
    boundingbox: [xMin - padX, yMax + padY, xMax + padX, yMin - padY],
    keepaspectratio: false,
    axis: true,
    showNavigation: false,
    showCopyright: false,
    pan: { enabled: false },
    zoom: { enabled: false },
    defaultAxes: {
      x: { name: `t [${figure.x_unit}]`, withLabel: true, label: { position: "rt", offset: [-40, 20] } },
      y: { name: `[${figure.y_unit}]`, withLabel: true, label: { position: "rt", offset: [10, -10] } },
    },
  });

  traces.forEach((trace, index) => {
    board.create("curve", [trace.samples.map(([x]) => Number(x)), trace.samples.map(([, y]) => Number(y))], {
      strokeColor: index === 0 ? "#1f6feb" : "#d29922",
      strokeWidth: 3,
      name: label(strings, trace.label_key, trace.label_key),
      withLabel: true,
      label: { position: "rt", offset: [6, -6] },
    });
  });

  markers.forEach((marker) => {
    const [x, y] = marker.at.map(Number);
    board.create("point", [x, y], {
      size: 4,
      face: "cross",
      strokeColor: "#c0392b",
      strokeWidth: 3,
      fixed: true,
      name: label(strings, marker.label_key, marker.label_key),
      withLabel: true,
      label: { offset: [-30, 18] },
    });
  });

  board.update();
  return board;
}
