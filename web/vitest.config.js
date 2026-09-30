import { defineConfig } from "vitest/config";

// The suite runs the real modules: config.js reaches KaTeX's stylesheet and
// JSXGraph through pages.js, which a bare `node --test` cannot resolve — the runner
// has to go through Vite's pipeline like the build does. jsdom is the environment the
// renderer is written for, so the assertions run against the DOM it actually builds.
export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["test/**/*.test.js"],
    // KaTeX's stylesheet is not under test; loading it costs a second and proves nothing.
    css: false,
    restoreMocks: true,
  },
});
