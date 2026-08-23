import { Router, Request, Response } from "express";

const BACKEND_TARGET = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export const proxyRouter = Router();

proxyRouter.use(async (req: Request, res: Response) => {
  const targetUrl = `${BACKEND_TARGET}/api/v1${req.path}`;
  const method = req.method;

  const headers: Record<string, string> = {};
  for (const [key, value] of Object.entries(req.headers)) {
    if (key.toLowerCase() === "host" || key.toLowerCase() === "content-length") continue;
    if (typeof value === "string") headers[key] = value;
    else if (Array.isArray(value)) headers[key] = value.join(", ");
  }

  let body: string | undefined = undefined;
  if (method !== "GET" && method !== "HEAD" && req.body && Object.keys(req.body).length > 0) {
    body = JSON.stringify(req.body);
    headers["content-type"] = "application/json";
  }

  try {
    const backendRes = await fetch(targetUrl, {
      method,
      headers,
      body,
    });

    res.status(backendRes.status);
    backendRes.headers.forEach((val, key) => {
      if (key.toLowerCase() !== "content-encoding" && key.toLowerCase() !== "transfer-encoding") {
        res.setHeader(key, val);
      }
    });

    const data = await backendRes.arrayBuffer();
    res.send(Buffer.from(data));
  } catch (err: any) {
    console.error(`[Proxy Error] Failed to connect to FastAPI backend at ${targetUrl}:`, err.message);
    res.status(502).json({
      success: false,
      error: {
        code: "BACKEND_UNREACHABLE",
        message: "Main FastAPI backend is unreachable on port 8000. Ensure backend service is running.",
        details: err.message,
      },
    });
  }
});
