import { spawn } from "node:child_process";

const chrome = spawn("/usr/bin/chromium", [
  "--headless=new",
  "--no-sandbox",
  "--disable-gpu",
  "--remote-debugging-port=9227",
  "--user-data-dir=/tmp/nyaya-headline-layout-cdp",
  "about:blank",
], { stdio: "ignore" });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function waitForDebugger() {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await fetch("http://127.0.0.1:9227/json/version");
      if (response.ok) return;
    } catch {}
    await sleep(100);
  }
  throw new Error("Chrome DevTools endpoint did not start");
}

async function openPage(url) {
  const response = await fetch(`http://127.0.0.1:9227/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!response.ok) throw new Error(`Could not open verification page: ${response.status}`);
  return response.json();
}

function connectCdp(url) {
  const socket = new WebSocket(url);
  const pending = new Map();
  let nextId = 1;
  socket.onmessage = event => {
    const payload = JSON.parse(event.data);
    const request = pending.get(payload.id);
    if (!request) return;
    pending.delete(payload.id);
    if (payload.error) request.reject(new Error(payload.error.message));
    else request.resolve(payload.result);
  };
  return new Promise((resolve, reject) => {
    socket.onopen = () => resolve({
      send(method, params = {}) {
        return new Promise((resolveRequest, rejectRequest) => {
          const id = nextId++;
          pending.set(id, { resolve: resolveRequest, reject: rejectRequest });
          socket.send(JSON.stringify({ id, method, params }));
        });
      },
      close() { socket.close(); },
    });
    socket.onerror = () => reject(new Error("Could not connect to Chrome DevTools"));
  });
}

async function measure(cdp, profile, theme) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: profile.width,
    height: profile.height,
    deviceScaleFactor: 1,
    mobile: profile.width <= 480,
  });
  await cdp.send("Page.navigate", { url: `http://127.0.0.1:3000/landing?theme=${theme}` });
  await sleep(850);
  const result = await cdp.send("Runtime.evaluate", {
    expression: `(() => {
      const heading = document.querySelector('.landing-hero-copy h1');
      const phrase = document.querySelector('.landing-hero-emphasis');
      const textWalker = document.createTreeWalker(heading, NodeFilter.SHOW_TEXT);
      const rowValues = [];
      let textNode = textWalker.nextNode();
      while (textNode) {
        const range = document.createRange();
        range.selectNodeContents(textNode);
        rowValues.push(...[...range.getClientRects()].map(rect => Math.round(rect.bottom)));
        textNode = textWalker.nextNode();
      }
      const rows = rowValues.sort((left, right) => left - right).reduce((lines, value) => {
        if (lines.length === 0 || Math.abs(value - lines[lines.length - 1]) > 4) lines.push(value);
        return lines;
      }, []);
      return {
        lineCount: rows.length,
        rowPositions: rows,
        phraseRectCount: phrase.getClientRects().length,
        overflows: heading.scrollWidth > heading.clientWidth + 1,
        headingWidth: Math.round(heading.clientWidth),
        headingHeight: Math.round(heading.clientHeight),
      };
    })()`,
    returnByValue: true,
  });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

const profiles = [
  { name: "wideLaptop", width: 1600, height: 817 },
  { name: "compactLaptop", width: 1366, height: 768 },
  { name: "mobile", width: 375, height: 812 },
];

try {
  await waitForDebugger();
  const page = await openPage("http://127.0.0.1:3000/landing?theme=light");
  const cdp = await connectCdp(page.webSocketDebuggerUrl);
  await cdp.send("Page.enable");
  const measurements = [];
  for (const profile of profiles) {
    for (const theme of ["light", "dark"]) {
      const layout = await measure(cdp, profile, theme);
      const desktopPass = profile.name !== "mobile" && layout.lineCount === 4 && layout.phraseRectCount === 1 && !layout.overflows;
      const mobilePass = profile.name === "mobile" && layout.lineCount >= 4 && !layout.overflows;
      if (!desktopPass && !mobilePass) throw new Error(`${profile.name} ${theme} headline composition did not meet the expected layout: ${JSON.stringify(layout)}`);
      measurements.push({ profile: profile.name, theme, ...layout });
    }
  }
  console.log(JSON.stringify({ measurements }, null, 2));
  cdp.close();
} finally {
  chrome.kill("SIGTERM");
}
