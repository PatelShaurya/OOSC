import type { Express } from "express";
import path from "path";
import fs from "fs";
import { ENV } from "./env";

export function registerStorageProxy(app: Express) {
  app.get("/manus-storage/*", async (req, res) => {
    const key = (req.params as Record<string, string>)[0];
    if (!key) {
      res.status(400).send("Missing storage key");
      return;
    }

    const localClientPath = path.resolve(process.cwd(), "client", "public", "manus-storage", key);
    const localDistPath = path.resolve(process.cwd(), "dist", "public", "manus-storage", key);

    if (fs.existsSync(localClientPath)) {
      return res.sendFile(localClientPath);
    }
    if (fs.existsSync(localDistPath)) {
      return res.sendFile(localDistPath);
    }

    if (!ENV.forgeApiUrl || !ENV.forgeApiKey) {
      res.status(404).send("Storage key not found locally");
      return;
    }

    try {
      const forgeUrl = new URL(
        "v1/storage/presign/get",
        ENV.forgeApiUrl.replace(/\/+$/, "") + "/",
      );
      forgeUrl.searchParams.set("path", key);

      const forgeResp = await fetch(forgeUrl, {
        headers: { Authorization: `Bearer ${ENV.forgeApiKey}` },
      });

      if (!forgeResp.ok) {
        const body = await forgeResp.text().catch(() => "");
        console.error(`[StorageProxy] forge error: ${forgeResp.status} ${body}`);
        res.status(502).send("Storage backend error");
        return;
      }

      const { url } = (await forgeResp.json()) as { url: string };
      if (!url) {
        res.status(502).send("Empty signed URL from backend");
        return;
      }

      res.set("Cache-Control", "no-store");
      res.redirect(307, url);
    } catch (err) {
      console.error("[StorageProxy] failed:", err);
      res.status(502).send("Storage proxy error");
    }
  });
}
