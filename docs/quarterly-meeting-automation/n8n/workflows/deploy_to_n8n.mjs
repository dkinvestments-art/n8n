#!/usr/bin/env node
/* Pushes every QMP workflow JSON to an n8n instance via the public API.
 *
 * Usage:
 *   N8N_BASE_URL=https://n8n.astuteadvisors.example \
 *   N8N_API_KEY=n8n_api_xxx \
 *   node deploy_to_n8n.mjs [--dir <folder>] [--activate] [--dry-run]
 *
 * Behavior:
 *   - Reads every *.workflow.json in the folder (default: this script's folder,
 *     plus ../Astute-*.workflow.json seed/example files if present).
 *   - Create-or-update by workflow NAME: if a workflow with the same name
 *     already exists on the instance, it is updated in place (same id, so the
 *     master's Run-node selections survive redeploys); otherwise it is created.
 *   - Sends only the fields the public API accepts: name, nodes, connections,
 *     settings. (Extra fields like meta are stripped — the API rejects them.)
 *   - --activate: activates workflows that have a schedule/poll trigger.
 *     Default OFF — activate manually after pasting credentials + IDs.
 *   - --dry-run: show the plan without writing anything.
 *
 * Requirements on the target instance: the n8n public API enabled (default)
 * and an API key (n8n UI -> Settings -> n8n API -> create key).
 */
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { dirname, join, basename } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (f) => args.includes(f);
const opt = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d; };

const BASE = (process.env.N8N_BASE_URL ?? "").replace(/\/+$/, "");
const KEY = process.env.N8N_API_KEY ?? "";
if (!BASE || !KEY) {
  console.error("Set N8N_BASE_URL and N8N_API_KEY environment variables.");
  console.error("  N8N_BASE_URL=https://your-n8n.example N8N_API_KEY=... node deploy_to_n8n.mjs");
  process.exit(2);
}

const dir = opt("--dir", HERE);
const files = readdirSync(dir).filter(f => f.endsWith(".workflow.json")).sort()
  .map(f => join(dir, f));
// include the seed + worked-example workflows from the parent folder when present
for (const extra of ["Astute-Seed-Automation-Sheets.workflow.json",
                     "Astute-QBO-Books-Health.workflow.json",
                     "Astute-Quarterly-Prep-Pipeline.workflow.json"]) {
  const p = join(dir, "..", extra);
  if (existsSync(p) && !files.some(f => basename(f) === extra)) files.push(p);
}

/* Transport: Node's fetch does NOT honor HTTPS_PROXY. In proxied sandboxes
 * (e.g. Claude Code cloud environments) we shell out to curl, which does —
 * and which also picks up any required CA bundle from the environment. */
import { execFileSync } from "node:child_process";
const USE_CURL = !!(process.env.HTTPS_PROXY || process.env.https_proxy) && !flag("--no-curl");

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const RETRY_STATUS = new Set([429, 502, 503, 504]); // transient: rate limit, gateway, DB-not-ready

// one request, returns { status, text }; never throws on HTTP status
const requestRaw = async (method, path, body) => {
  const url = BASE + "/api/v1" + path;
  const headers = { "X-N8N-API-KEY": KEY, "content-type": "application/json", accept: "application/json" };
  if (USE_CURL) {
    const args = ["-sS", "--max-time", "60", "-X", method, url,
                  "-H", "X-N8N-API-KEY: " + KEY, "-H", "content-type: application/json",
                  "-H", "accept: application/json", "-w", "\n__HTTP_STATUS__:%{http_code}"];
    if (body !== undefined) args.push("--data-binary", JSON.stringify(body));
    let out;
    try { out = execFileSync("curl", args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 }); }
    catch (e) { return { status: 0, text: String(e.stderr || e.message || e) }; } // curl transport error
    const m = out.match(/\n__HTTP_STATUS__:(\d+)\s*$/);
    return { status: m ? Number(m[1]) : 0, text: m ? out.slice(0, m.index) : out };
  }
  try {
    const res = await fetch(url, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
    return { status: res.status, text: await res.text() };
  } catch (e) { return { status: 0, text: String(e.message || e) }; }
};

// api() with automatic retry on transient statuses (503 "Database is not ready!", 429, gateways)
const api = async (method, path, body, { retries = 5 } = {}) => {
  let attempt = 0, last;
  while (true) {
    const { status, text } = await requestRaw(method, path, body);
    last = { status, text };
    if (status >= 200 && status < 300) {
      try { return JSON.parse(text); } catch { return { raw: text }; }
    }
    const transient = status === 0 || RETRY_STATUS.has(status);
    if (transient && attempt < retries) {
      const wait = Math.min(1000 * 2 ** attempt, 16000);
      console.error("  transient " + status + " on " + method + " " + path + " — retry in " + (wait / 1000) + "s (" + (attempt + 1) + "/" + retries + ")");
      await sleep(wait); attempt++; continue;
    }
    throw new Error(method + " " + path + " -> " + status + ": " + String(text).slice(0, 300));
  }
};

// block until n8n's API + database are ready (Railway cold-start / DB warmup)
const waitForReady = async (maxSeconds = 180) => {
  const deadline = Date.now() + maxSeconds * 1000;
  let announced = false;
  while (Date.now() < deadline) {
    const { status } = await requestRaw("GET", "/workflows?limit=1");
    if (status >= 200 && status < 300) { if (announced) console.log("n8n is ready."); return; }
    if (status === 401 || status === 403) throw new Error("Auth failed (" + status + ") — check N8N_API_KEY / its scopes.");
    if (!announced) { console.log("Waiting for n8n to be ready (last status " + status + ")..."); announced = true; }
    await sleep(3000);
  }
  throw new Error("n8n not ready after " + maxSeconds + "s — check the instance / its database (Railway Postgres service).");
};

// wait for the instance + DB before doing anything (unless just previewing offline)
if (!flag("--dry-run")) await waitForReady();

// map existing workflows by name (paginate)
const existing = new Map();
let cursor;
do {
  const page = await api("GET", "/workflows?limit=100" + (cursor ? "&cursor=" + cursor : ""));
  for (const w of page.data ?? []) existing.set(w.name, w.id);
  cursor = page.nextCursor;
} while (cursor);
console.log("Target: " + BASE + "  (existing workflows: " + existing.size + ")");

const SCHEDULE_TYPES = ["n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.gmailTrigger"];
let created = 0, updated = 0, activated = 0, failed = 0;

for (const file of files) {
  const raw = JSON.parse(readFileSync(file, "utf8"));
  const body = { name: raw.name, nodes: raw.nodes, connections: raw.connections,
                 settings: raw.settings ?? {} };
  const label = basename(file);
  try {
    if (flag("--dry-run")) {
      console.log((existing.has(raw.name) ? "would UPDATE " : "would CREATE ") + raw.name + "  [" + label + "]");
      continue;
    }
    let id;
    if (existing.has(raw.name)) {
      id = existing.get(raw.name);
      await api("PUT", "/workflows/" + id, body);
      updated++; console.log("UPDATED  " + raw.name);
    } else {
      const res = await api("POST", "/workflows", body);
      id = res.id;
      created++; console.log("CREATED  " + raw.name + "  (id " + id + ")");
    }
    const hasSchedule = raw.nodes.some(n => SCHEDULE_TYPES.includes(n.type));
    if (flag("--activate") && hasSchedule) {
      await api("POST", "/workflows/" + id + "/activate");
      activated++; console.log("         activated (has schedule trigger)");
    }
  } catch (e) {
    failed++; console.error("FAILED   " + raw.name + "  [" + label + "]: " + e.message);
  }
}

console.log("\nDone: " + created + " created, " + updated + " updated, " +
            activated + " activated, " + failed + " failed, " + files.length + " total.");
if (!flag("--activate")) console.log("Note: nothing was activated. After pasting credentials + sheet IDs, activate the master + ops workflows in the n8n UI (or re-run with --activate).");
process.exit(failed ? 1 : 0);
