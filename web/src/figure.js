// Figure JSON -> JSXGraph. The browser only draws what the server decided.
// Vendored prebuilt bundle: JSXGraph's `exports` field does not expose
// ./distrib/*, and its ESM entry is ~40 side-effect imports (not tree-shakeable),
// so the distrib files are committed and imported directly (research recommendation).
import JXG from "../vendor/jsxgraphcore.js";
import "../vendor/jsxgraph.css";

const LABELS = {
  "trace.position": "s(t)",
  "trace.velocity": "v(t)",
};

function label(strings, key, fallback) {
  return strings?.[key] ?? fallback ?? key;
}

export function renderFigure(container, figure, strings) {
  const domain = figure.domain ?? { t_min: "0", t_max: "1" };
  const tMax = Number(domain.t_max) + 1;

  const board = JXG.JSXGraph.initBoard(container, {
    boundingbox: [-0.5, 1, tMax + 0.5, -1],
    axis: true,
    showNavigation: false,
    showCopyright: false,
    defaultAxes: {
      x: { name: `${label(strings, "axis.time", "t")} [${figure.x_unit}]`, withLabel: true },
      y: { name: `[${figure.y_unit}]`, withLabel: true },
    },
  });

  const curves = (figure.traces ?? []).map((trace, index) => {
    const xs = trace.samples.map(([x]) => Number(x));
    const ys = trace.samples.map(([, y]) => Number(y));
    return board.create("curve", [xs, ys], {
      strokeColor: index === 0 ? "#1f6feb" : "#d29922",
      strokeWidth: 3,
      name: label(strings, trace.label_key, LABELS[trace.label_key] ?? trace.label_key),
      withLabel: true,
      label: { position: "rt" },
    });
  });

  (figure.markers ?? []).forEach((marker) => {
    const [x, y] = marker.at.map(Number);
    board.create("point", [x, y], {
      size: 4,
      color: "#c0392b",
      fixed: true,
      name: label(strings, marker.label_key, marker.label_key),
      withLabel: true,
      label: { offset: [8, 8] },
    });
  });

  // rescale once the real data extent is known
  const allY = (figure.traces ?? []).flatMap((t) => t.samples.map(([, y]) => Number(y)))
    .concat((figure.markers ?? []).map((m) => Number(m.at[1])));
  if (allY.length) {
    const maxY = Math.max(...allY);
    const minY = Math.min(...allY);
    board.setBoundingBox([-0.5, maxY + Math.abs(maxY) * 0.15 + 1, tMax + 0.5, minY - Math.abs(maxY || 1) * 0.15 - 1], true);
  }

  return board;
}
