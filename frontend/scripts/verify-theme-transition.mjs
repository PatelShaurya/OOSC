import { spawn } from "node:child_process";

const chrome = spawn("/usr/bin/chromium", [
  "--headless=new",
  "--no-sandbox",
  "--disable-gpu",
  "--remote-debugging-port=9223",
  "--user-data-dir=/tmp/nyaya-theme-cdp",
  "about:blank",
], { stdio: "ignore" });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function waitForDebugger() {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await fetch("http://127.0.0.1:9223/json/version");
      if (response.ok) return;
    } catch {}
    await sleep(100);
  }
  throw new Error("Chrome DevTools endpoint did not start");
}

async function openPage(url) {
  const response = await fetch(`http://127.0.0.1:9223/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!response.ok) throw new Error(`Could not open test page: ${response.status}`);
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

async function value(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function testAtViewport(cdp, width, height) {
  await cdp.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width <= 480 });
  await value(cdp, "new Promise(resolve => setTimeout(resolve, 50))");
  const modeTest = await value(cdp, `(() => {
    const toggle = document.querySelector('.theme-toggle');
    const before = toggle?.innerText.trim();
    toggle?.click();
    return new Promise(resolve => setTimeout(() => resolve({ before, afterFirst: toggle?.innerText.trim(), transitionClass: document.querySelector('.app-shell')?.className, overlay: document.querySelector('.theme-veil')?.innerText.trim() }), 80));
  })()`);
  const reverseTest = await value(cdp, `(() => {
    const toggle = document.querySelector('.theme-toggle');
    toggle?.click();
    return new Promise(resolve => setTimeout(() => resolve({ afterSecond: toggle?.innerText.trim(), transitionClass: document.querySelector('.app-shell')?.className, overlay: document.querySelector('.theme-veil')?.innerText.trim() }), 80));
  })()`);
  return { width, modeTest, reverseTest };
}

try {
  await waitForDebugger();
  const page = await openPage("http://127.0.0.1:3000/landing?theme=light");
  const cdp = await connectCdp(page.webSocketDebuggerUrl);
  await cdp.send("Page.enable");
  await cdp.send("Page.navigate", { url: "http://127.0.0.1:3000/landing?theme=light" });
  await sleep(900);
  const desktop = await testAtViewport(cdp, 1280, 720);
  await cdp.send("Page.navigate", { url: "http://127.0.0.1:3000/landing?theme=light" });
  await sleep(900);
  const mobile = await testAtViewport(cdp, 375, 812);
  await cdp.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  await cdp.send("Page.navigate", { url: "http://127.0.0.1:3000/landing?theme=light" });
  await sleep(900);
  const reducedMotion = await value(cdp, `(() => {
    const toggle = document.querySelector('.theme-toggle');
    toggle?.click();
    return new Promise(resolve => setTimeout(() => resolve({ mode: toggle?.innerText.trim(), transitionClass: document.querySelector('.app-shell')?.className, overlay: document.querySelector('.theme-veil')?.innerText.trim() }), 80));
  })()`);
  console.log(JSON.stringify({ desktop, mobile, reducedMotion }, null, 2));
  cdp.close();
} finally {
  chrome.kill("SIGTERM");
}
