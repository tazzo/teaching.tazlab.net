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

/**
 * kind: graph_reading — the graph carries the answer; the steps show how to read it.
 *
 * On a mill page (`page.bare_graph`) the teacher states the question in person, so the
 * card is the drawing and nothing else. The figure arrives in its `bare` form, which is
 * what keeps the rest away: no marker naming the asked instant, no phase naming the kind
 * of motion (and so no legend), no per-kind colour code. What is left to read is the
 * shape of the graph.
 */
export function renderGraphReadingPage(item, index, context) {
  const { strings, page } = context;
  const t = translate(strings);
  const card = el("article", "card");
  const bare = page?.bare_graph === true;
  const { header, statement } = cardHeader(item, index);
  if (bare) {
    card.append(header);
  } else {
    statement.append(renderText(t(item.statement.key, item.statement.key), item.statement.params));
    header.append(statement);
    card.append(header);
  }
  if (item.figure) {
    const host = el("div", "figure");
    card.append(host);
    renderFigure(host, item.figure, strings);
    const legend = segmentLegend(item.figure, t);
    if (legend) card.append(legend);
  }
  if (!bare) card.append(stepsBlock(item, t), answerBlock(item, t));
  return card;
}

/**
 * A figure built from segments names them: the colours match the traces, so the student
 * can tell which part of the graph the statement is talking about.
 */
function segmentLegend(figure, t) {
  const phases = figure?.phases ?? [];
  if (phases.length < 2) return null;              // one segment needs no legend
  const list = el("ul", "figure-legend");
  phases.forEach((phase) => {
    const item_ = el("li", `legend-item kind-${phase.kind}`);
    item_.append(el("span", "legend-swatch", ""));
    item_.append(el("span", null, t(phase.label_key, phase.kind)));
    item_.append(el("span", "legend-range",
      `${phase.t_from}–${phase.t_to} ${figure.x_unit}`));
    list.append(item_);
  });
  return list;
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
  const checkButton = el("button", "btn btn-quiet", t("ui.check"));
  const revealButton = el("button", "btn btn-quiet", t("ui.reveal"));
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

/**
 * kind: multiple_choice — multiple choice fill-in-the-blank question with instant feedback.
 *
 * The card is a question and four options; nothing says which one is right until the
 * student has answered. «Mostra la soluzione» is the way out for a student who does not
 * know: it marks the right option and brings the reason with it, because a solution
 * without its «perché» teaches the answer and not the grammar. The steps (clue and rule)
 * are appended only after an answer or a reveal: they are the answer's own explanation,
 * and on the German cards the rule names the right form in so many words.
 */
export function renderMultipleChoicePage(item, index, context) {
  const { strings } = context;
  const t = translate(strings);
  const card = el("article", "card multiple-choice-card");
  const { header, statement } = cardHeader(item, index);
  statement.append(renderText(t(item.statement.key, item.statement.key), item.statement.params));
  header.append(statement);
  card.append(header);

  const payload = item.answer?.payload ?? {};
  const options = payload.options ?? [];
  const correctAnswer = payload.correct?.[0] ?? "";
  const explanation = payload.explanation?.[0] ?? "";

  const choiceList = el("div", "choice-list");
  choiceList.setAttribute("role", "radiogroup");

  const letters = ["A", "B", "C", "D", "E", "F"];
  let selectedOption = null;
  const optionButtons = [];

  const status = el("div", "choice-status");

  options.forEach((optText, optIndex) => {
    const btn = el("button", "choice-option");
    btn.type = "button";
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", "false");

    const letterSpan = el("span", "choice-letter", letters[optIndex] ?? String(optIndex + 1));
    const textSpan = el("span", "choice-text", optText);
    btn.append(letterSpan, textSpan);

    btn.addEventListener("click", () => {
      if (card.dataset.checked === "true") return;
      optionButtons.forEach((b) => {
        b.classList.remove("selected");
        b.setAttribute("aria-checked", "false");
      });
      btn.classList.add("selected");
      btn.setAttribute("aria-checked", "true");
      selectedOption = optText;
      status.replaceChildren();
      status.className = "choice-status";
    });

    optionButtons.push(btn);
    choiceList.append(btn);
  });

  card.append(choiceList);

  const actions = el("div", "page-actions");
  const checkBtn = el("button", "btn btn-quiet", t("ui.check_answer", "Verifica"));
  checkBtn.type = "button";
  // The solution is a door, not a printed line: the student may open it when she is stuck,
  // and until she does (or until she checks) nothing on the card says which option is right.
  // The reason travels with the solution, because «perché» is the point of the card.
  const revealBtn = el("button", "btn btn-quiet", t("ui.reveal", "Mostra la soluzione"));
  revealBtn.type = "button";
  const retryBtn = el("button", "btn btn-quiet", t("ui.try_again", "Riprova"));
  retryBtn.type = "button";
  retryBtn.style.display = "none";
  actions.append(checkBtn, revealBtn, retryBtn);
  card.append(actions, status);

  // The two steps carry the rule that decides the answer, and on 44 of the 45 German
  // choice cards that rule spells the right form out loud. They are therefore appended
  // only after the answer — a `<details>` in the DOM before it is the solution one tap
  // away, and the payload is not a hiding place.
  let stepsNode = null;
  const revealSteps = () => {
    if (stepsNode || !item.steps?.length) return;
    stepsNode = stepsBlock(item, t);
    card.append(stepsNode);
  };
  const hideSteps = () => {
    stepsNode?.remove();
    stepsNode = null;
  };

  checkBtn.addEventListener("click", () => {
    if (!selectedOption) {
      status.textContent = t("ui.select_an_option", "Seleziona un'opzione prima di verificare.");
      status.className = "choice-status bad";
      return;
    }

    card.dataset.checked = "true";
    checkBtn.style.display = "none";
    revealBtn.style.display = "none";
    retryBtn.style.display = "";

    const isCorrect = selectedOption.trim() === correctAnswer.trim();
    optionButtons.forEach((btn) => {
      const btnText = btn.querySelector(".choice-text")?.textContent?.trim();
      btn.disabled = true;
      if (btnText === correctAnswer.trim()) {
        btn.classList.add("choice-correct");
      } else if (btn.classList.contains("selected")) {
        btn.classList.add("choice-incorrect");
      }
    });

    status.replaceChildren();
    if (isCorrect) {
      status.className = "choice-status good";
      const badge = el("strong", "status-badge", `✓ ${t("ui.correct", "Corretto!")}`);
      status.append(badge);
    } else {
      status.className = "choice-status bad";
      const badge = el("strong", "status-badge", `✗ ${t("ui.incorrect", "Non corretto")}`);
      status.append(badge);
    }

    if (explanation) {
      const explP = el("p", "choice-explanation", explanation);
      status.append(explP);
    }
    revealSteps();
  });

  revealBtn.addEventListener("click", () => {
    if (card.dataset.checked === "true") return;
    card.dataset.checked = "true";
    checkBtn.style.display = "none";
    revealBtn.style.display = "none";
    retryBtn.style.display = "";
    optionButtons.forEach((btn) => {
      btn.disabled = true;
      if (btn.querySelector(".choice-text")?.textContent?.trim() === correctAnswer.trim()) {
        btn.classList.add("choice-correct");
      }
    });
    status.replaceChildren();
    status.className = "choice-status";
    status.append(el("p", "choice-hint", t("ui.solution_is", "La soluzione è: {answer}")
      .replace("{answer}", correctAnswer)));
    if (explanation) status.append(el("p", "choice-explanation", explanation));
    revealSteps();
  });

  retryBtn.addEventListener("click", () => {
    card.dataset.checked = "false";
    selectedOption = null;
    optionButtons.forEach((btn) => {
      btn.disabled = false;
      btn.classList.remove("selected", "choice-correct", "choice-incorrect");
      btn.setAttribute("aria-checked", "false");
    });
    checkBtn.style.display = "";
    revealBtn.style.display = "";
    retryBtn.style.display = "none";
    hideSteps();
    status.replaceChildren();
    status.className = "choice-status";
  });

  return card;
}

/**
 * kind: classification_choice — the kind of sentence is a question of its own.
 *
 * The sibling page writes the classification inside every option ("who (defining)"), which
 * gives the answer away: the right kind is the one that repeats across the four options, so
 * it can be read off the pattern without ever looking at the commas. Here the options are
 * bare pronouns and the kind is asked separately, under the sentence:
 *
 *   [ defining ] [ non-defining ]        <- nothing is checkable until one is chosen
 *
 * The check button is born `disabled` and, while it is, a line under it says why: the lock
 * has to be visible before the click, not an error after it. `data-classification` on each
 * selector button is the value compared with `payload.classification[0]`; the server checks
 * the same grammar in `verify()`, so the lock is a teaching device, not the only guard.
 *
 * The picker is **data, not a layout**: which question is asked, which two values answer it
 * and the two lines under the buttons all travel in the payload
 * (`classification_values` and `classification_labels`, `classification_prompt_key`,
 * `classification_locked_key`, `classification_wrong_key`, `option_wrong_key`). That is
 * what lets the same interaction host a different grammar — the kind of a relative clause
 * on one page, the kind of verb (action against state) then the form on another — without
 * a second renderer or a copy of this one. The defining/non-defining pair stays as the
 * fallback: a card whose payload lost the field must stay answerable, and that pair is what
 * the page that predates the data-driven picker asks.
 */
const DEFAULT_KIND_CHOICES = [
  { value: "defining", label_key: "ui.classification_defining" },
  { value: "non-defining", label_key: "ui.classification_non_defining" },
];

/** The two parallel lists the payload carries, as one list of {value, label_key}. */
function kindChoicesOf(payload) {
  const values = payload.classification_values ?? [];
  const labels = payload.classification_labels ?? [];
  if (!values.length) return DEFAULT_KIND_CHOICES;
  return values.map((value, i) => ({ value, label_key: labels[i] ?? value }));
}

export function renderClassificationChoicePage(item, index, context) {
  const { strings } = context;
  const t = translate(strings);
  const card = el("article", "card multiple-choice-card classification-card");
  const { header, statement } = cardHeader(item, index);
  statement.append(renderText(t(item.statement.key, item.statement.key), item.statement.params));
  header.append(statement);
  card.append(header);

  const payload = item.answer?.payload ?? {};
  const options = payload.options ?? [];
  const correctAnswer = payload.correct?.[0] ?? "";
  const correctClassification = payload.classification?.[0] ?? "";
  const explanation = payload.explanation?.[0] ?? "";
  // what the selector asks, and what it offers: the payload decides, the pair of the
  // relative page is only the fallback for a payload that does not say.
  const kindChoices = kindChoicesOf(payload);
  const promptKey = payload.classification_prompt_key?.[0] ?? "ui.classification_prompt";
  const lockedKey = payload.classification_locked_key?.[0] ?? "ui.classification_locked";
  const wrongKindKey = payload.classification_wrong_key?.[0] ?? "ui.classification_wrong";
  const wrongOptionKey = payload.option_wrong_key?.[0] ?? "ui.pronoun_wrong";

  let selectedOption = null;
  let selectedClassification = null;
  const optionButtons = [];
  const classificationButtons = [];

  // --- the kind: the first question, and the lock on the second ------------------
  const kindHost = el("div", "classification-picker");
  const kindPrompt = t(promptKey, "Che tipo di frase \u00e8 questa?");
  kindHost.append(el("p", "classification-prompt", kindPrompt));
  const kindGroup = el("div", "classification-choices");
  kindGroup.setAttribute("role", "radiogroup");
  kindGroup.setAttribute("aria-label", kindPrompt);

  kindChoices.forEach((choice) => {
    const { value, label_key: labelKey } = choice;
    const btn = el("button", "classification-option");
    btn.type = "button";
    btn.dataset.classification = value;
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", "false");
    btn.append(el("span", "classification-text", t(labelKey, value)));
    btn.addEventListener("click", () => {
      if (card.dataset.checked === "true") return;
      classificationButtons.forEach((other) => {
        other.classList.remove("selected");
        other.setAttribute("aria-checked", "false");
      });
      btn.classList.add("selected");
      btn.setAttribute("aria-checked", "true");
      selectedClassification = value;
      status.replaceChildren();
      status.className = "choice-status";
      syncLock();
    });
    classificationButtons.push(btn);
    kindGroup.append(btn);
  });
  kindHost.append(kindGroup);
  card.append(kindHost);

  // --- the pronoun: the multiple choice the other grammar pages already draw -----
  const choiceList = el("div", "choice-list");
  const letters = ["A", "B", "C", "D", "E", "F"];

  options.forEach((optText, optIndex) => {
    const btn = el("button", "choice-option");
    btn.type = "button";
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", "false");

    const letterSpan = el("span", "choice-letter", letters[optIndex] ?? String(optIndex + 1));
    const textSpan = el("span", "choice-text", optText);
    btn.append(letterSpan, textSpan);

    btn.addEventListener("click", () => {
      if (card.dataset.checked === "true") return;
      optionButtons.forEach((other) => {
        other.classList.remove("selected");
        other.setAttribute("aria-checked", "false");
      });
      btn.classList.add("selected");
      btn.setAttribute("aria-checked", "true");
      selectedOption = optText;
      status.replaceChildren();
      status.className = "choice-status";
    });

    optionButtons.push(btn);
    choiceList.append(btn);
  });

  choiceList.setAttribute("role", "radiogroup");
  card.append(choiceList);

  const status = el("div", "choice-status");
  const lockedHint = el("p", "classification-hint",
    t(lockedKey, "Scegli il tipo: finch\u00e9 non scegli, la verifica resta bloccata."));

  const actions = el("div", "page-actions");
  const checkBtn = el("button", "btn btn-quiet", t("ui.check_answer", "Verifica"));
  checkBtn.type = "button";
  const retryBtn = el("button", "btn btn-quiet", t("ui.try_again", "Riprova"));
  retryBtn.type = "button";
  retryBtn.style.display = "none";
  actions.append(checkBtn, retryBtn);
  card.append(actions, lockedHint, status);

  /** The lock and its visible reason travel together: one without the other is a puzzle. */
  function syncLock() {
    const locked = selectedClassification === null;
    checkBtn.disabled = locked;
    checkBtn.setAttribute("aria-disabled", String(locked));
    lockedHint.hidden = !locked;
  }

  checkBtn.addEventListener("click", () => {
    // a disabled button does not fire; the guard is for keyboard and programmatic clicks
    if (selectedClassification === null || !selectedOption) return;

    card.dataset.checked = "true";
    checkBtn.style.display = "none";
    retryBtn.style.display = "";
    lockedHint.hidden = true;

    // the second fact is a form on one page and a pronoun on another: the payload
    // decides which line reports it, so the variable says "option", not "pronoun".
    const optionRight = selectedOption.trim() === correctAnswer.trim();
    const kindRight = selectedClassification === correctClassification;

    optionButtons.forEach((btn) => {
      const btnText = btn.querySelector(".choice-text")?.textContent?.trim();
      btn.disabled = true;
      if (btnText === correctAnswer.trim()) {
        btn.classList.add("choice-correct");
      } else if (btn.classList.contains("selected")) {
        btn.classList.add("choice-incorrect");
      }
    });
    classificationButtons.forEach((btn) => {
      btn.disabled = true;
      if (btn.dataset.classification === correctClassification) {
        btn.classList.add("classification-correct");
      } else if (btn.dataset.classification === selectedClassification) {
        btn.classList.add("classification-incorrect");
      }
    });

    status.replaceChildren();
    if (optionRight && kindRight) {
      status.className = "choice-status good";
      status.append(el("strong", "status-badge", `\u2713 ${t("ui.correct", "Corretto!")}`));
    } else {
      status.className = "choice-status bad";
      status.append(el("strong", "status-badge", `\u2717 ${t("ui.incorrect", "Non corretto")}`));
      // two facts were asked, so the sentence says which one fell
      if (!kindRight) {
        status.append(el("p", "choice-hint", t(wrongKindKey, "Il tipo non \u00e8 quello giusto.")));
      }
      if (!optionRight) {
        status.append(el("p", "choice-hint", t(wrongOptionKey, "La risposta non \u00e8 quella giusta.")));
      }
    }
    if (explanation) status.append(el("p", "choice-explanation", explanation));
  });

  retryBtn.addEventListener("click", () => {
    card.dataset.checked = "false";
    selectedOption = null;
    selectedClassification = null;
    optionButtons.forEach((btn) => {
      btn.disabled = false;
      btn.classList.remove("selected", "choice-correct", "choice-incorrect");
      btn.setAttribute("aria-checked", "false");
    });
    classificationButtons.forEach((btn) => {
      btn.disabled = false;
      btn.classList.remove("selected", "classification-correct", "classification-incorrect");
      btn.setAttribute("aria-checked", "false");
    });
    checkBtn.style.display = "";
    retryBtn.style.display = "none";
    status.replaceChildren();
    status.className = "choice-status";
    syncLock();                       // a second attempt starts locked again
  });

  syncLock();                         // the page opens locked, not after a first mistake

  if (item.steps && item.steps.length) {
    card.append(stepsBlock(item, t));
  }

  return card;
}

/**
 * The comparison the completion field makes: forgiving about case, extra spaces and a
 * final full stop, and about nothing else. The spellings themselves are data — the
 * payload's `accept` list, which starts with the solution — so a card that also takes
 * «heisse» for «heiße» says so itself and the client never holds a German word.
 */
export function normaliseCompletion(value) {
  return String(value ?? "")
    .normalize("NFC")
    .replace(/\s+/gu, " ")
    .trim()
    .replace(/[.,!?;:]+$/u, "")
    .toLowerCase();
}

/**
 * kind: completion_choice — a sentence with a gap; the missing word is typed in, or
 * picked among four.
 *
 * The page kind is one because the exercise is one: a German sentence with a hole in it,
 * a control under it, and the reason that appears once the student has answered. The
 * card's payload says which of the two ways it is answered (`format`), so no page carries
 * a second layout and no list of pages has to be split by format. The four-option branch
 * IS the multiple choice the site already had — `renderMultipleChoicePage`, called as it
 * is — so the two cannot drift apart.
 *
 * The completion branch, and why it is built this way:
 *
 *   Ich ______ aus Italien.        <- the gap is in the sentence (the topic's data)
 *   [ komme            ] Verifica  <- Enter in the field checks, as the button does
 *   La risposta è: komme           <- only after a wrong answer
 *   Perché è «komme»…              <- the reason, after the answer, never before
 *
 * The reasons (the card's two steps) are appended **after the check**, not before: on a
 * completion the rule that explains the form is a conjugation table, and a table above an
 * empty field is the answer written beside it — the lesson of the relative-clause page.
 * Feedback is a word and a mark (✓ / ✗), not a colour alone; the status is an `aria-live`
 * region so a screen reader hears the verdict; and everything is reachable from the
 * keyboard because it is a form with a submit button, not a div with a click handler.
 */
export function renderCompletionChoicePage(item, index, context) {
  const { strings } = context;
  const t = translate(strings);
  const payload = item.answer?.payload ?? {};
  const format = payload.format?.[0] ?? (payload.options?.length ? "choice" : "completion");
  if (format === "choice") return renderMultipleChoicePage(item, index, context);

  const card = el("article", "card completion-card");
  const { header, statement } = cardHeader(item, index);
  statement.append(renderText(t(item.statement.key, item.statement.key), item.statement.params));
  header.append(statement);
  card.append(header);

  const solution = payload.correct?.[0] ?? "";
  const accepted = (payload.accept?.length ? payload.accept : [solution])
    .map(normaliseCompletion)
    .filter(Boolean);
  const explanation = payload.explanation?.[0] ?? "";

  const fieldId = `completion-${index + 1}`;
  const form = el("form", "completion-form");
  form.noValidate = true;

  const label = el("label", "completion-field");
  label.htmlFor = fieldId;
  label.append(el("span", "completion-label", t("ui.completion_label", "La parola che manca")));
  const input = el("input", "completion-input");
  input.type = "text";
  input.id = fieldId;
  input.autocomplete = "off";
  input.spellcheck = false;
  input.setAttribute("autocapitalize", "off");
  input.setAttribute("aria-describedby", `${fieldId}-hint`);
  input.placeholder = t("ui.completion_placeholder", "scrivi la parola in tedesco");
  label.append(input);
  form.append(label);

  const hint = el("p", "completion-hint", t("ui.completion_hint", "Basta una parola."));
  hint.id = `${fieldId}-hint`;
  form.append(hint);

  const actions = el("div", "page-actions");
  const checkBtn = el("button", "btn btn-quiet", t("ui.check_answer", "Verifica"));
  checkBtn.type = "submit";
  const retryBtn = el("button", "btn btn-quiet", t("ui.try_again", "Riprova"));
  retryBtn.type = "button";
  retryBtn.hidden = true;
  actions.append(checkBtn, retryBtn);
  form.append(actions);
  card.append(form);

  const status = el("div", "choice-status");
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  card.append(status);

  let stepsNode = null;
  const revealSteps = () => {
    if (stepsNode || !item.steps?.length) return;
    stepsNode = stepsBlock(item, t);
    card.append(stepsNode);
  };
  const hideSteps = () => {
    stepsNode?.remove();
    stepsNode = null;
  };

  const finish = (right) => {
    input.disabled = true;
    checkBtn.hidden = true;
    retryBtn.hidden = false;
    status.replaceChildren();
    status.className = right ? "choice-status good" : "choice-status bad";
    status.append(el("strong", "status-badge",
      right ? `\u2713 ${t("ui.completion_correct", "Giusto!")}`
            : `\u2717 ${t("ui.completion_wrong", "Non è giusto.")}`));
    if (!right) {
      const line = t("ui.completion_answer", "La risposta è: {answer}")
        .replace("{answer}", solution);
      status.append(el("p", "choice-hint", line));
    }
    if (explanation) status.append(el("p", "choice-explanation", explanation));
    revealSteps();
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (input.disabled) return;
    const typed = normaliseCompletion(input.value);
    if (!typed) {
      status.replaceChildren();
      status.className = "choice-status bad";
      status.append(el("p", "choice-hint",
        t("ui.completion_empty", "Scrivi la parola che manca, poi verifica.")));
      input.focus();
      return;
    }
    finish(accepted.includes(typed));
  });

  retryBtn.addEventListener("click", () => {
    input.disabled = false;
    input.value = "";
    checkBtn.hidden = false;
    retryBtn.hidden = true;
    // the rule goes with the answer: leaving it on screen would hand the retry the word
    hideSteps();
    status.replaceChildren();
    status.className = "choice-status";
    input.focus();
  });

  return card;
}

/**
 * kind: schede_list — the sheets, each behind its stable address.
 *
 * Not an exercise: nothing is generated and nothing is answered. One row per sheet with
 * its link, and, under it, the version that link is serving today — the date, the commit
 * and the sha256 of the bytes. The address never changes, so the version has to be said:
 * without that line a saved link would be a promise nobody can check. `updated` with no
 * `commit` is a real state (the PDF knows when it was compiled, git does not travel into
 * the image) and it is said as "compilata il", never dressed up as a commit.
 */
export function renderSchedeList(schede, context) {
  const t = translate(context?.strings);
  const fill = (text, values) => text.replace(/\{(\w+)\}/g, (match, key) =>
    (values[key] === undefined ? match : String(values[key])));

  const list = el("ul", "schede-list");
  schede.forEach((scheda) => {
    const item = el("li", "scheda");
    item.dataset.scheda = scheda.id;

    item.append(el("h3", "scheda-title", scheda.title));
    if (scheda.subtitle) item.append(el("p", "scheda-subtitle", scheda.subtitle));

    // the version: the line that tells today's sheet from yesterday's
    const meta = el("p", "scheda-meta");
    const version = scheda.updated
      ? (scheda.commit
        ? fill(t("ui.schede_updated"), { date: scheda.updated, commit: scheda.commit })
        : fill(t("ui.schede_compiled"), { date: scheda.updated }))
      : t("ui.schede_undeclared");
    meta.append(el("span", "scheda-version", version));
    meta.append(el("span", "scheda-size",
      fill(t("ui.schede_size"), { kb: Math.max(1, Math.round(scheda.bytes / 1024)) })));
    item.append(meta);

    // the link: the stable address, and it is a plain href on purpose — a PDF is not a
    // route of this app, and `download` gives the file a name a teacher recognises
    const actions = el("p", "scheda-actions");
    const link = el("a", "btn btn-primary", t("ui.schede_open"));
    link.href = scheda.url;
    link.setAttribute("download", scheda.file.split("/").pop());
    actions.append(link);

    const hash = el("span", "scheda-hash");
    hash.append(el("span", "scheda-hash-label", t("ui.schede_sha")));
    hash.append(el("code", null, scheda.sha256));
    actions.append(hash);
    item.append(actions, el("p", "scheda-hint", t("ui.schede_verify")));

    list.append(item);
  });
  return list;
}

const RENDERERS = {
  problem: renderProblemPage,
  graph_reading: renderGraphReadingPage,
  graph_filling: renderGraphFillingPage,
  multiple_choice: renderMultipleChoicePage,
  classification_choice: renderClassificationChoicePage,
  completion_choice: renderCompletionChoicePage,
};


export function renderItemForKind(kind, item, index, context) {
  const renderer = RENDERERS[kind] ?? renderProblemPage;
  return renderer(item, index, context);
}
