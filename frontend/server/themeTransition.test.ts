import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";

describe("Nyaya theme handoff", () => {
  it("keeps the bold motion sequence separate from the reduced-motion path", async () => {
    const app = await readFile(new URL("../client/src/App.tsx", import.meta.url), "utf8");
    const css = await readFile(new URL("../client/src/index.css", import.meta.url), "utf8");

    expect(app).toContain('window.matchMedia("(prefers-reduced-motion: reduce)")');
    expect(app).toContain("setDark(nextDark)");
    expect(app).toContain("theme-shift-${themeTransition}");
    expect(css).toContain("theme-shutter-dark");
    expect(css).toContain("theme-shutter-light");
    expect(css).toContain("@media (prefers-reduced-motion:no-preference)");
  });
});
