// Page renderers — one per exercise kind. A page's layout is its kind's layout.
import { renderFigure } from "./figure.js";
import { renderFormula, renderText } from "./formula.js";

export function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function translate(strings) {
  return (key, fallback) => strings?.[key] ?? fallback ?? key;
}

function cardHeader(item, index) {
  const header = el("header", "card-header");
  header.append(el("span", "badge", `#${index + 1}`));
  const statement = el("p", "statement");
  return { header, statement };
}

function stepsBlock(item, t) {
  const steps = el("details", "steps");
  steps.append(el("summary", null, t("ui.steps")));
  item.steps.forEach((step) => {
    const row = el("div", "step");
    row.append(el("span", "step-label", t(step.label_key, step.label_key)));
    row.append(renderFormula(step.latex));
    steps.append(row);
  });
  return steps;
}

function answerBlock(item, t) {
  const answer = el("div", "answer");
  answer.append(el("span", "answer-label", t("ui.answer")));
  answer.append(renderFormula(item.answer.latex, true));
  return answer;
}

/** kind: problem — statement, steps, answer. */
export function renderProblemPage(item, index, context) {
  const { strings } = context;
  const t = translate(strings);
  const card = el("article", "card");
  const { header, statement } = cardHeader(item, index);
  statement.append(renderText(t(item.statement.key, item.statement.key), item.statement.params));
  header.append(statement);
  card.append(header, stepsBlock(item, t), answerBlock(item, t));
  return card;
}

/** kind: graph_reading — the graph carries the answer; the steps show how to read it. */
export function renderGraphReadingPage(item, index, context) {
  const { strings } = context;
  const t = translate(strings);
  const card = el("article", "card");
  const { header, statement } = cardHeader(item, index);
  statement.append(renderText(t(item.statement.key, item.statement.key), item.statement.params));
  header.append(statement);
  card.append(header);
  if (item.figure) {
    const host = el("div", "figure");
    card.append(host);
    renderFigure(host, item.figure, strings);
  }
  card.append(stepsBlock(item, t), answerBlock(item, t));
  return card;
}

/**
 * kind: graph_filling — the problem data are given and the graph starts empty.
 * The student places points on the grid, checks them against the model, and can reveal
 * the solution. The model is fetched from the same seed, so it is the same item.
 */
export function renderGraphFillingPage(item, index, context) {
  const { strings, model } = context;
  const t = translate(strings);
  const card = el("article", "card");
  const { header, statement } = cardHeader(item, index);
  statement.append(renderText(t(item.statement.key, item.statement.key), item.statement.params));
  header.append(statement);
  card.append(header);

  const host = el("div", "figure fillable");
  card.append(host);
  const board = renderFigure(host, item.figure, strings);   // empty axes: no traces, no markers

  const placed = [];
  const status = el("p", "status");
  const hint = el("p", "hint", t("ui.fill_hint"));
  const checkButton = el("button", null, t("ui.check"));
  const revealButton = el("button", null, t("ui.reveal"));
  checkButton.type = "button";
  revealButton.type = "button";
  const actions = el("div", "page-actions");
  actions.append(checkButton, revealButton);
  card.append(hint, actions, status);
  let revealed = false;

  if (board) {
    let index_ = 0;
    board.on("down", (event) => {
      const coords = board.getUsrCoordsOfMouse(event);
      if (!coords || !coords.length) return;
      const [x, y] = coords;
      const point = board.create("point", [x, y], {
        size: 3, face: "cross", strokeColor: "#1f6feb", strokeWidth: 3, fixed: true,
      });
      placed.push(point);
      index_ += 1;
      status.textContent = t("ui.points_placed").replace("{n}", String(index_));
    });
  }

  const solutions = () => {
    const traces = model?.figure?.traces ?? [];
    const samples = traces[0]?.samples ?? [];
    return samples.map(([x, y]) => [Number(x), Number(y)]);
  };

  const nearModel = (point) => {
    const samples = solutions();
    if (samples.length < 2) return false;
    const [[x1, y1], [x2, y2]] = [samples[0], samples[samples.length - 1]];
    const dx = x2 - x1;
    if (dx === 0) return false;
    const expected = y1 + ((y2 - y1) * (point.X() - x1)) / dx;
    const span = Math.max(1, Math.abs(y2 - y1));
    return Math.abs(point.Y() - expected) / span < 0.05;   // 5% of the value range
  };

  checkButton.addEventListener("click", () => {
    if (!placed.length) {
      status.textContent = t("ui.fill_hint");
      return;
    }
    const wrong = placed.filter((point) => !nearModel(point)).length;
    status.textContent = wrong === 0 ? t("ui.all_correct") : t("ui.some_wrong");
    status.classList.toggle("bad", wrong !== 0);
  });

  // The answer and the derivation stay hidden until the student asks for them: a
  // "fill the graph" exercise whose solution is printed underneath is not an exercise.
  revealButton.addEventListener("click", () => {
    if (revealed) return;
    revealed = true;
    revealButton.disabled = true;
    if (model?.figure) {
      const host2 = el("div", "figure");
      card.append(host2);
      renderFigure(host2, model.figure, strings);
    }
    card.append(stepsBlock(item, t), answerBlock(item, t));
  });

  return card;
}

const RENDERERS = {
  problem: renderProblemPage,
  graph_reading: renderGraphReadingPage,
  graph_filling: renderGraphFillingPage,
};

export function renderItemForKind(kind, item, index, context) {
  const renderer = RENDERERS[kind] ?? renderProblemPage;
  return renderer(item, index, context);
}
