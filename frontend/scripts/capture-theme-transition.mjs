import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const chrome = spawn("/usr/bin/chromium", [
  "--headless=new",
  "--no-sandbox",
  "--disable-gpu",
  "--remote-debugging-port=9224",
  "--user-data-dir=/tmp/nyaya-theme-capture-cdp",
  "about:blank",
], { stdio: "ignore" });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function waitForDebugger() {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await fetch("http://127.0.0.1:9224/json/version");
      if (response.ok) return;
    } catch {}
    await sleep(100);
  }
  throw new Error("Chrome DevTools endpoint did not start");
}

async function openPage(url) {
  const response = await fetch(`http://127.0.0.1:9224/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!response.ok) throw new Error(`Could not open capture page: ${response.status}`);
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

async function captureAt(cdp, initialTheme, outputPath) {
  await cdp.send("Page.navigate", { url: `http://127.0.0.1:3000/landing?theme=${initialTheme}` });
  await sleep(900);
  await cdp.send("Runtime.evaluate", { expression: "document.querySelector('.theme-toggle')?.click()" });
  await sleep(260);
  const screenshot = await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(outputPath, Buffer.from(screenshot.data, "base64"));
}

try {
  await waitForDebugger();
  const page = await openPage("http://127.0.0.1:3000/landing?theme=light");
  const cdp = await connectCdp(page.webSocketDebuggerUrl);
  await cdp.send("Page.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
  await captureAt(cdp, "light", "/tmp/nyaya-theme-dark-transition.png");
  await captureAt(cdp, "dark", "/tmp/nyaya-theme-light-transition.png");
  cdp.close();
} finally {
  chrome.kill("SIGTERM");
}
