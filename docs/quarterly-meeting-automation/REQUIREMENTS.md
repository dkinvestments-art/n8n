# QMP — Full Requirements & Remaining Work

**Status date:** 2026-07-10
**Bottom line:** the software is 100% built and validated. What's left is
**deployment wiring and data entry** — roughly a half-day of focused setup,
almost all of it in web UIs (n8n, Google, QBO) that only the firm can do
because it involves live Astute credentials.

Legend: ✅ done · 🔶 in progress · ⬜ remaining · (owner → est. time)

---

## A. Software (build) — ✅ COMPLETE

- ✅ 21 QMP n8n workflows (13 pipeline subs, 6 ops, master orchestrator, ops-sheet seeder)
- ✅ Seed workflow for the 3 data sheets + Books Health worked example
- ✅ Strategy Library seed content (36 strategies, importable)
- ✅ Claude prompts + JSON schemas for all 8 AI nodes (embedded in workflows)
- ✅ API deployer (`deploy_to_n8n.mjs`) — proxy-aware, DB-readiness wait,
  transient-5xx retry; verified against a live n8n (24/24, idempotent)
- ✅ Validation suite (`validate.js`) — all 21 pass
- ✅ Documentation: DEPLOYMENT.md, DATA-GOVERNANCE.md, spec v2.0, compliance guide

Nothing further to build. Everything below is configuration + data.

## B. Infrastructure — 🔶 MOSTLY THERE

- ✅ n8n instance running (Railway: n8n-custom-production.up.railway.app)
- 🔶 **Postgres stability** — deploy attempt hit `503 Database is not ready!`.
  Verify the Railway Postgres service is awake/healthy and consider disabling
  Railway's app sleeping for both services; the schedule triggers (6h master,
  daily/weekly ops) need the instance awake. (you → 15 min)
- ⬜ Confirm the n8n URL is reachable from Karen's browser (approval-email
  links resolve to it). (you → 2 min)

## C. Deploy the workflows — 🔶 IN PROGRESS

- 🔶 Run `node deploy_to_n8n.mjs` from your Mac (clone is already in
  `/Users/dmac/Claude/n8n`; `git pull` first for the hardened deployer).
  Expected: **24 created, 0 failed**. The script now waits out DB warmup.
  (you → 5 min once the DB is up)
- ⬜ **Rotate the n8n API key** after deploying (it's in chat history):
  n8n → Settings → n8n API. (you → 2 min)

## D. Credentials in n8n — ⬜ NOT STARTED (all Astute accounts)

Create once in n8n → Credentials, then select on the imported nodes
(every node shows a `REPLACE_ASTUTE_*` placeholder):

- ⬜ Google OAuth2 — Sheets, Docs, Drive, Calendar, Gmail, Slides (needs a
  Google Cloud OAuth client with those APIs enabled; n8n's credential setup
  walks through it). (Karen/you → 30-45 min, the fiddliest step)
- ⬜ Anthropic API key (console.anthropic.com — Astute org). (→ 5 min)
- ⬜ QuickBooks Online OAuth2 (Intuit developer app → production keys;
  connect once, per-client access via `qbo_realm_id`). (→ 20 min)
- ⬜ Karbon API token (HTTP Header Auth credential). (→ 10 min)
- ⬜ Fathom API key (HTTP Header Auth credential). (→ 5 min)

Optional/deferred: GoHighLevel (fallback emails), Gamma (nicer decks),
Blue J (no public API — used manually, results pasted into research memos).

## E. Data layer — ⬜ NOT STARTED

- ⬜ Run **Astute-Seed-Automation-Sheets** (needs Google credential + the
  Astute "Automations" folder ID pasted into its Config node) → creates
  Strategy Library (36 rows), Client Strategy Status, Client Profile Matrix.
  (→ 10 min)
- ⬜ Run **QMP-00b** → creates the 9-tab QMP Operations sheet. (→ 2 min)
- ⬜ Add `qbo_realm_id` column to the Client Profile Matrix. (→ 2 min)
- ⬜ Create the **briefs folder** in Astute Drive. (→ 1 min)
- ⬜ Build the **deck template** in Google Slides with the 13 `{{PLACEHOLDER}}`
  text boxes (list in DEPLOYMENT.md §4). (→ 20-30 min, quality matters —
  this is the client-facing artifact)

## F. Configuration — ⬜ NOT STARTED

- ⬜ Paste the **8 shared IDs** into the imported workflows (profile sheet,
  library sheet, status sheet, ops sheet, Karen email, Christina email,
  briefs folder, deck template). (→ 15 min)
- ⬜ **Wire the master**: open QMP-MASTER, select the matching sub-workflow in
  each of the 13 "Run:" dropdowns (one-time; n8n assigns IDs at import).
  (→ 10 min)
- ⬜ **Activate**: ops workflows (08, 09a, 10, 11, 16) + the master. Leave
  09b manual. (→ 5 min)

## G. Content the firm must supply — ⬜ NOT STARTED

- ⬜ **Karen reviews the Strategy Library** and flips rows Draft →
  Firm-Approved (screener ignores everything else; verify OBBBA-dated items).
  (Karen → 30-45 min, one time)
- ⬜ **Per-client profile rows** — for each client: name, entity type, state,
  `qbo_realm_id`, `karbon_client_id`, client email, `gmail_query_alias`,
  Drive folder links (general, tax, PMT). Start with ONE client. (→ 10 min/client)
- ⬜ Optional now / grows later: Rules tab entries (rules engine), pay stubs
  in client folders (payroll stays manual by design).

## H. Validation run — ⬜ THE FINAL GATE

- ⬜ One-client end-to-end test per DEPLOYMENT.md §6: calendar event
  "Quarterly — <client>" ~48h out → watch the master execute → approve →
  confirm brief, deck, payment rows, Karbon item, run log. (you + Karen → 1-2 h
  including fix-ups)
- ⬜ **Expected fix-ups during this run** (known, bounded — DEPLOYMENT.md
  caveats): Karbon/Fathom response field names in the Format/Match Code
  nodes; possible n8n node-parameter drift (Google Docs insert, Sheets
  update-by-row, Gmail draft); QBO covers `Purchase` transactions initially.
  These are per-node tweaks, not structural work.

## I. Housekeeping — ⬜ SMALL BUT REAL

- ⬜ Delete the two stray files on the **personal** Drive from early testing
  ("Automations" folder + "Client Strategy Status" sheet) — per
  DATA-GOVERNANCE. (you → 1 min)
- ⬜ Attorney review of the NDA/Service Agreement — **only if** you still
  engage the third-party developer; self-deploying makes these optional.
- ⬜ Mirror the data-governance rule into Karen's Obsidian (I have no vault
  access; copy from DATA-GOVERNANCE.md).

## Ongoing (once live)

- **Anthropic API usage** — the only meaningful new recurring cost
  (~10 Claude calls per client prep, several on Opus-tier; expect a few
  dollars per prep, plus weekly reclass/rules runs).
- Railway hosting for n8n + Postgres (existing).
- Karen's recurring touchpoints per prep: 2-min input reply (optional),
  brief review + approve click, reclassification approvals, and promoting
  proposed strategies/rules — the human-in-the-loop by design.

---

## Critical path (do in this order)

1. **B** Railway Postgres healthy → **C** deploy 24 workflows → rotate key
2. **D** Google + Anthropic credentials (unlocks everything else)
3. **E** seed sheets → **F** paste IDs + wire master
4. **D** remaining credentials (QBO, Karbon, Fathom) + **E** deck template
5. **G** Karen: approve strategies + one client row
6. **H** one-client validation run → fix the small stuff → go live

Total remaining effort: ≈ **4-6 hours** of hands-on setup spread across
you and Karen, plus the validation run.
