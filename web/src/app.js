// Minimal configurator: pick a topic, generate, read the graph.
import strings from "./i18n/it.json";
import { renderFigure } from "./figure.js";
import { renderFormula, renderText } from "./formula.js";

const state = { catalog: null };

const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

async function loadCatalog() {
  const response = await fetch("/api/catalog");
  state.catalog = await response.json();
  const select = document.getElementById("topic");
  select.replaceChildren(
    ...state.catalog.topics.map((topic) => {
      const option = el("option", null, strings[`topic.${topic.id}`] ?? topic.id);
      option.value = topic.id;
      return option;
    }),
  );
  syncDifficulties();
}

function currentTopic() {
  const id = document.getElementById("topic").value;
  return state.catalog.topics.find((t) => t.id === id);
}

function syncDifficulties() {
  const topic = currentTopic();
  const select = document.getElementById("difficulty");
  select.replaceChildren(
    ...(topic?.difficulties ?? []).map((difficulty) => {
      const option = el("option", null, strings[`difficulty.${difficulty}`] ?? difficulty);
      option.value = difficulty;
      return option;
    }),
  );
}

function renderItem(item, index) {
  const card = el("article", "card");
  const header = el("header", "card-header");
  header.append(el("span", "badge", `#${index + 1}`));

  const topic = currentTopic();
  const statement = el("p", "statement");
  const template = strings[item.statement.key] ?? item.statement.key;
  statement.append(renderText(template, item.statement.params));
  header.append(statement);
  card.append(header);

  const figureHost = el("div", "figure");
  card.append(figureHost);
  renderFigure(figureHost, item.figure, strings);

  const steps = el("details", "steps");
  steps.append(el("summary", null, strings["ui.steps"]));
  item.steps.forEach((step) => {
    const row = el("div", "step");
    row.append(el("span", "step-label", strings[step.label_key] ?? step.label_key));
    row.append(renderFormula(step.latex));
    steps.append(row);
  });
  card.append(steps);

  const answer = el("div", "answer");
  answer.append(el("span", "answer-label", strings["ui.answer"]));
  answer.append(renderFormula(item.answer.latex, true));
  card.append(answer);

  return card;
}

async function generate() {
  const status = document.getElementById("status");
  const results = document.getElementById("results");
  const topic = currentTopic();
  const difficulty = document.getElementById("difficulty").value;
  const seed = Number(document.getElementById("seed").value) || 1;
  const count = Number(document.getElementById("count").value) || 3;

  status.textContent = strings["ui.loading"];
  results.replaceChildren();
  try {
    const url = `/api/generate?topic=${encodeURIComponent(topic.id)}&difficulty=${difficulty}&seed=${seed}&count=${count}`;
    const response = await fetch(url);
    const body = await response.json();
    if (!response.ok) {
      status.textContent = `${strings["ui.error"]}: ${body?.error?.code ?? response.status}`;
      return;
    }
    status.textContent = "";
    body.items.forEach((item, index) => results.append(renderItem(item, index)));
  } catch (error) {
    status.textContent = `${strings["ui.error"]}: ${error}`;
  }
}

function main() {
  document.title = strings["ui.title"];
  document.getElementById("title").textContent = strings["ui.title"];
  [
    ["topic", "ui.topic"],
    ["difficulty", "ui.difficulty"],
    ["seed", "ui.seed"],
    ["count", "ui.count"],
    ["generate", "ui.generate"],
  ].forEach(([id, key]) => {
    const target = id === "generate" ? document.getElementById(id) : document.querySelector(`label[for="${id}"]`);
    if (target) target.textContent = strings[key];
  });
  document.getElementById("seed").value = String(Math.floor(Math.random() * 1e6));
  document.getElementById("topic").addEventListener("change", syncDifficulties);
  document.getElementById("generate").addEventListener("click", generate);
  document.getElementById("status").textContent = strings["ui.empty"];
  loadCatalog().catch((error) => {
    document.getElementById("status").textContent = `Catalog: ${error}`;
  });
}

main();
