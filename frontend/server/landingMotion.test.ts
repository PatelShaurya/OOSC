import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";

describe("Nyaya replayable motion", () => {
  it("uses shared intersection targets that can reset, replay, and respect reduced motion", async () => {
    const app = await readFile(new URL("../client/src/App.tsx", import.meta.url), "utf8");
    const css = await readFile(new URL("../client/src/index.css", import.meta.url), "utf8");

    expect(app).toContain("IntersectionObserver");
    expect(app).toContain("scroll-replay");
    expect(app).toContain("classList.toggle(\"is-visible\", entry.isIntersecting)");
    expect(app).toContain("scroll-motion-ready");
    expect(app).toContain('rights-options scroll-replay');
    expect(app).toContain('document-row scroll-replay');
    expect(app).toContain('paper-kicker scroll-replay');
    expect(app).toContain("prefers-reduced-motion: reduce");
    expect(css).toContain("Shared replayable section motion");
    expect(css).toContain(".scroll-motion-ready .scroll-replay.is-visible");
    expect(css).toContain("@media (prefers-reduced-motion:reduce)");
  });
});
