import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const chrome = spawn("/usr/bin/chromium", [
  "--headless=new",
  "--no-sandbox",
  "--disable-gpu",
  "--remote-debugging-port=9225",
  "--user-data-dir=/tmp/nyaya-landing-motion-cdp",
  "about:blank",
], { stdio: "ignore" });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function waitForDebugger() {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await fetch("http://127.0.0.1:9225/json/version");
      if (response.ok) return;
    } catch {}
    await sleep(100);
  }
  throw new Error("Chrome DevTools endpoint did not start");
}

async function openPage(url) {
  const response = await fetch(`http://127.0.0.1:9225/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
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

async function value(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function navigateAndMeasure(cdp, width, height, capturePath) {
  await cdp.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width <= 480 });
  await cdp.send("Page.navigate", { url: "http://127.0.0.1:3000/landing?theme=light" });
  await sleep(900);
  await value(cdp, "document.documentElement.scrollTop = 0; document.body.scrollTop = 0; new Promise(resolve => setTimeout(resolve, 180))");
  const initial = await value(cdp, `(() => ({
    ready: document.querySelector('.app-shell')?.classList.contains('scroll-motion-ready'),
    total: document.querySelectorAll('.scroll-replay').length,
    visible: document.querySelectorAll('.scroll-replay.is-visible').length,
    progress: getComputedStyle(document.querySelector('.landing-progress span')).getPropertyValue('transform')
  }))()`);
  await value(cdp, "document.documentElement.scrollTop = Math.round(document.documentElement.scrollHeight * 0.46); document.body.scrollTop = Math.round(document.documentElement.scrollHeight * 0.46); new Promise(resolve => setTimeout(resolve, 850))");
  const screenshot = await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(capturePath, Buffer.from(screenshot.data, "base64"));
  const middle = await value(cdp, `(() => ({
    visible: document.querySelectorAll('.scroll-replay.is-visible').length,
    progress: getComputedStyle(document.querySelector('.landing-progress span')).getPropertyValue('transform')
  }))()`);
  await value(cdp, "document.documentElement.scrollTop = document.documentElement.scrollHeight; document.body.scrollTop = document.documentElement.scrollHeight; new Promise(resolve => setTimeout(resolve, 950))");
  const final = await value(cdp, `(() => ({
    visible: document.querySelectorAll('.scroll-replay.is-visible').length,
    total: document.querySelectorAll('.scroll-replay').length,
    progress: getComputedStyle(document.querySelector('.landing-progress span')).getPropertyValue('transform')
  }))()`);
  const replay = await value(cdp, `(() => {
    const target = document.querySelector('.landing-wayfinding');
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    return new Promise(resolve => setTimeout(() => {
      const reset = !target?.classList.contains('is-visible');
      target?.scrollIntoView({ block: 'center' });
      setTimeout(() => resolve({ reset, replayed: Boolean(target?.classList.contains('is-visible')) }), 850);
    }, 700));
  })()`);
  return { width, initial, middle, final, replay };
}

async function verifyRoute(cdp, path) {
  await cdp.send("Page.navigate", { url: `http://127.0.0.1:3000${path}?theme=light` });
  await sleep(path === "/assistant" ? 1300 : 900);
  return value(cdp, `(() => ({
    path: location.pathname,
    ready: document.querySelector('.app-shell')?.classList.contains('scroll-motion-ready'),
    targets: document.querySelectorAll('.scroll-replay').length,
    visible: document.querySelectorAll('.scroll-replay.is-visible').length
  }))()`);
}

async function verifyMobileRouteScroll(cdp, path, targetSelector, verifyReplay = false) {
  await cdp.send("Page.navigate", { url: `http://127.0.0.1:3000${path}?theme=light` });
  await sleep(path === "/assistant" ? 1300 : 900);
  return value(cdp, `(() => {
    const target = document.querySelector(${JSON.stringify(targetSelector)});
    const count = () => ({
      total: [...document.querySelectorAll('.scroll-replay')].filter(element => element.offsetParent !== null).length,
      visible: [...document.querySelectorAll('.scroll-replay.is-visible')].filter(element => element.offsetParent !== null).length
    });
    const before = count();
    const initiallyVisible = Boolean(target?.classList.contains('is-visible'));
    target?.scrollIntoView({ block: 'center' });
    return new Promise(resolve => setTimeout(() => {
      const entered = Boolean(target?.classList.contains('is-visible'));
      if (!${verifyReplay}) return resolve({ path: location.pathname, target: ${JSON.stringify(targetSelector)}, before, initiallyVisible, entered, afterEntry: count() });
      const maxScroll = document.documentElement.scrollHeight - innerHeight;
      window.scrollTo(0, Math.min(maxScroll, (target?.offsetTop || 0) + (target?.offsetHeight || 0) + innerHeight));
      setTimeout(() => {
        const reset = !target?.classList.contains('is-visible');
        target?.scrollIntoView({ block: 'center' });
        setTimeout(() => resolve({ path: location.pathname, target: ${JSON.stringify(targetSelector)}, before, initiallyVisible, entered, reset, replayed: Boolean(target?.classList.contains('is-visible')), afterEntry: count() }), 800);
      }, 700);
    }, 800));
  })()`);
}

try {
  await waitForDebugger();
  const page = await openPage("http://127.0.0.1:3000/landing?theme=light");
  const cdp = await connectCdp(page.webSocketDebuggerUrl);
  await cdp.send("Page.enable");
  await cdp.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
  const desktop = await navigateAndMeasure(cdp, 1280, 720, "/tmp/nyaya-landing-scroll-desktop.png");
  const mobile = await navigateAndMeasure(cdp, 375, 812, "/tmp/nyaya-landing-scroll-mobile.png");
  await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
  const routes = [];
  for (const path of ["/dashboard", "/assistant", "/rights", "/documents", "/documents/complaint"]) {
    routes.push(await verifyRoute(cdp, path));
  }
  await cdp.send("Emulation.setDeviceMetricsOverride", { width: 375, height: 812, deviceScaleFactor: 1, mobile: true });
  const mobileRoutes = [];
  for (const path of ["/dashboard", "/assistant", "/rights", "/documents", "/documents/complaint"]) {
    mobileRoutes.push(await verifyRoute(cdp, path));
  }
  const mobileScrollThrough = [];
  for (const [path, target, replay] of [
    ["/dashboard", ".activity", false],
    ["/assistant", ".case-main .case-section:nth-of-type(2)", true],
    ["/rights", ".rights-options button:nth-child(6)", false],
    ["/documents", ".document-row:nth-of-type(3)", false],
    ["/documents/complaint", ".paper p:nth-of-type(7)", false],
  ]) {
    mobileScrollThrough.push(await verifyMobileRouteScroll(cdp, path, target, replay));
  }
  await cdp.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  await cdp.send("Page.navigate", { url: "http://127.0.0.1:3000/landing?theme=light" });
  await sleep(900);
  const reducedMotion = await value(cdp, `(() => ({
    ready: document.querySelector('.app-shell')?.classList.contains('scroll-motion-ready'),
    visible: document.querySelectorAll('.scroll-replay.is-visible').length,
    total: document.querySelectorAll('.scroll-replay').length
  }))()`);
  console.log(JSON.stringify({ desktop, mobile, routes, mobileRoutes, mobileScrollThrough, reducedMotion }, null, 2));
  cdp.close();
} finally {
  chrome.kill("SIGTERM");
}
