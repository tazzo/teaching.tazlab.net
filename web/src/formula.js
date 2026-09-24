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

export function renderText(template, params) {
  return template.replace(/\{(\w+)\}/g, (_, key) => (params?.[key] ?? "?"));
}
