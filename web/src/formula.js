// KaTeX rendering — the one place formulas become HTML in the browser.
import katex from "katex";
import "katex/dist/katex.min.css";

export function renderFormula(latex, displayMode = false) {
  const span = document.createElement("span");
  try {
    katex.render(latex, span, { displayMode, throwOnError: false, strict: false });
  } catch (error) {
    // throwOnError is false so this is defensive only; never show a broken formula silently
    span.textContent = latex;
    span.classList.add("formula-error");
    span.title = String(error);
  }
  return span;
}

/**
 * Templates use `{key}` for a raw value and `{+key}` when the value needs an explicit
 * sign — otherwise a negative constant renders as "+ -12" in an equation. The minus is
 * U+2212, which is the character KaTeX also renders, so screen and PDF agree.
 */
export function renderText(template, params) {
  return template
    .replace(/\{\+(\w+)\}/g, (_, key) => signed(params?.[key]))
    .replace(/\{(\w+)\}/g, (_, key) => typographic(params?.[key]));
}

/** Render a leading ASCII hyphen as U+2212, the character KaTeX uses, so a coefficient
 *  reads as a maths minus rather than a dash: "-6x" becomes "−6x". */
function typographic(value) {
  if (value === undefined || value === null) return "?";
  const text = String(value);
  return text.startsWith("-") ? `\u2212${text.slice(1)}` : text;
}

function signed(value) {
  if (value === undefined || value === null) return "?";
  const text = String(value);
  const negative = text.startsWith("-");
  const magnitude = negative ? text.slice(1) : text;
  return `${negative ? "\u2212" : "+"} ${magnitude}`;
}
