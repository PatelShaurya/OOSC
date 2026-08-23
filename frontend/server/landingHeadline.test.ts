import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";

describe("Nyaya landing headline", () => {
  it("keeps the emphasized phrase together when responsive widths change", async () => {
    const app = await readFile(new URL("../client/src/App.tsx", import.meta.url), "utf8");
    const css = await readFile(new URL("../client/src/index.css", import.meta.url), "utf8");

    expect(app).toContain('<span className="landing-hero-line">When the</span><br/><span className="landing-hero-line">system</span><br/><span className="landing-hero-emphasis">feels <em>too&nbsp;much,</em></span><br/><span className="landing-hero-line">start here.</span>');
    expect(css).toContain("max-width:780px");
    expect(css).toContain("font-size:clamp(68px,7vw,118px)");
    expect(css).toContain(".landing-hero-emphasis { white-space:nowrap; }");
  });
});
