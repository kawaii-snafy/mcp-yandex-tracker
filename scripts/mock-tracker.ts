/**
 * A stand-in for api.tracker.yandex.net for smoke tests: logs every request the
 * server would have sent and answers `{}`, so even `tracker_call` can be driven
 * with fake credentials. Point the server at it with
 * YANDEX_TRACKER_BASE_URL=http://127.0.0.1:8787.
 *
 *   MOCK_PORT    listen port (8787)
 *   MOCK_STATUS  status of every reply (200) — 429 or 5xx exercises the retries
 *   MOCK_DELAY   milliseconds before replying (0) — above the timeout exercises it
 */

import { createServer } from "node:http";
import { setTimeout as sleep } from "node:timers/promises";

const port = Number(process.env.MOCK_PORT ?? 8787);
const status = Number(process.env.MOCK_STATUS ?? 200);
const delay = Number(process.env.MOCK_DELAY ?? 0);

createServer(async (req, res) => {
  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const org = req.headers["x-cloud-org-id"] ?? req.headers["x-org-id"];
  console.log(`${req.method} ${req.url} org=${org}`, Buffer.concat(chunks).toString());

  await sleep(delay);
  res.writeHead(status, { "content-type": "application/json" }).end("{}");
}).listen(port, () => console.log(`mock Tracker on http://127.0.0.1:${port}`));
