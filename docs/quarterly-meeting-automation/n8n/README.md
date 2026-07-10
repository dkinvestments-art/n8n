# n8n Workflows — Astute Advisors Quarterly Prep

This folder contains **two importable n8n workflows**, both authenticated as
Karen's Astute account (per `../DATA-GOVERNANCE.md` — no personal account is
ever used):

1. **`Astute-Seed-Automation-Sheets.workflow.json`** — one-time seed that
   creates the three automation sheets in her Drive (documented below).
2. **`Astute-Quarterly-Prep-Pipeline.workflow.json`** — the main v2.0 prep
   pipeline **scaffold** (documented at the bottom).

Run the seed workflow first (it creates the sheets the pipeline reads).

---

## Seed Workflow — Automation Sheets

Creates the three automation Google Sheets directly in **Karen's Astute
Advisors Google Drive**, authenticated as her Astute account.

## What it creates

| Sheet | Seeded content |
|-------|----------------|
| **Tax Strategy Library** | All 36 strategies (from `../strategy-library/Strategy-Library.csv`) |
| **Client Strategy Status** | Header row (per-client tracking; ready for data) |
| **Client Profile Matrix** | Headers + one EXAMPLE row (delete after review) |

## Files

- `Astute-Seed-Automation-Sheets.workflow.json` — the importable workflow
- `Client-Profile-Matrix.csv`, `Client-Strategy-Status.csv` — source data (also embedded in the workflow)
- `build_seed_workflow.py` — regenerates the workflow JSON from the CSVs (run if you edit the CSVs)

The workflow is **self-contained**: each CSV is embedded (base64) inside a Code
node and parsed at run time, so there are no external file dependencies.

## Import & run (5 minutes, done inside Karen's n8n)

1. **Import**: in Karen's n8n → Workflows → Import from File → choose
   `Astute-Seed-Automation-Sheets.workflow.json`.
2. **Credential**: on each Google node (6 total — the Create/Move/Append nodes),
   select **Karen's Astute Advisors Google credential**. If it doesn't exist
   yet, create one OAuth credential signed in as her Astute Workspace account
   and select it on all of them. The JSON ships with a placeholder credential
   named "Karen Astute Advisors Google" as a reminder.
3. **Folder**: create (or pick) an **Automations** folder in Karen's Astute
   Drive, copy its folder ID from the URL
   (`drive.google.com/drive/folders/<THIS_ID>`), and paste it into the
   **Config (set Astute folder ID)** node.
4. **Run once** with "Run once to seed sheets". The three sheets appear in the
   Astute Automations folder.
5. **Tidy up**: delete the single blank row in Client Strategy Status and the
   EXAMPLE row in Client Profile Matrix.

## Important notes

- **Governance**: because every Google node uses Karen's Astute credential and
  the target is her Astute folder, all three sheets are created and owned on
  Astute infrastructure. The personal account is never used.
- **Validation run**: this workflow was authored and its embedded data/parsing
  were verified, but it could **not** be executed against Karen's live n8n from
  the build environment. The developer should do one validation run and confirm
  the Google **Sheets create / Drive move / Sheets append** node parameters
  match the installed n8n version (node schemas occasionally shift between
  versions). The embedded CSV data and Code-node parsing are confirmed correct
  (Library = 36 rows, Profile = 1 example row).
- **Re-running** creates fresh copies each time (it does not overwrite). Run
  once; if you need to re-seed, delete the prior sheets first.
- **Editing the library later**: edit the CSV, re-run `build_seed_workflow.py`,
  re-import — or just edit the live Google Sheet directly (the ongoing intake
  paths in the screener spec write there anyway).

---

## Main Pipeline — Quarterly Prep (v2.0 scaffold)

`Astute-Quarterly-Prep-Pipeline.workflow.json` — an importable blueprint of the
full v2.0 pipeline (35 nodes across 5 phases). Regenerate with
`build_main_pipeline.py`.

### What is real vs. placeholder

**Real and functional** (imports and runs as a skeleton):
- Schedule trigger → Google Calendar (events 24-72h out) → filter for
  "Quarterly" → Client Profile Matrix lookup → Build Context
- Control flow through all phases
- **Approval gate** (Wait node, resume-on-webhook) → `Approved?` IF branch
- Output wiring: deck → Karbon tasks → payment reminders → run log; the
  not-approved path loops back to revise the brief

**Placeholders you complete** (each is a labeled node with a TODO / sticky
note pointing to the Developer Requirements Spec):
- Ingestion: Karbon work items, client email digest, Fathom transcript recap,
  QBO financials/aging/uncategorized + books health, tax-document extraction,
  client file inventory + PMT, preparer input prompt
- AI analysis: strategy screener, tax estimate + entity comparison, scorecard
- Deck generation (Slides or Gamma) and Karbon task creation

### Setup

1. Import the JSON into Karen's n8n.
2. Select **Karen's Astute Advisors Google credential** on every Google /
   Gmail node.
3. Replace every `PASTE_*` value:
   - `PASTE_CLIENT_PROFILE_MATRIX_SHEET_ID`, `PASTE_TAX_STRATEGY_LIBRARY_SHEET_ID`,
     `PASTE_RUN_LOG_SHEET_ID` (from the seed workflow's sheets)
   - `PASTE_ASTUTE_CLIENT_FOLDER_ID`, `PASTE_KAREN_EMAIL`
4. Complete each placeholder ingestion / AI node with its API call + Claude
   prompt (Developer Requirements Spec, Sub-Workflows 1, 6, 12-20).
5. In production, fan the Phase ② ingestion nodes into parallel branches with a
   Merge before Phase ③ (the scaffold runs them in sequence for readability).

### Same caveat as the seed workflow

Authored against current n8n and structurally validated (JSON valid, all
connections resolve, approval gate branches correctly), but **not executed
against Karen's live n8n**. The developer should validate node parameters
against the installed n8n version and complete the placeholders before
production use. This is the blueprint to build against — not a finished,
runnable-end-to-end automation.

---

## AI Node Prompts — `Claude-Prompts.md`

Production-ready Claude prompts for every AI node in the main pipeline (email
digest, transcript recap, tax position extract, books health, strategy screener,
tax estimate + entity comparison, scorecard, and the Meeting Brief compiler).

Each entry gives the exact **Anthropic Messages API** call for an n8n HTTP Request
node: system prompt, user prompt (with `{{ }}` placeholders), a JSON Schema for
`output_config.format` (structured outputs, so n8n gets reliable JSON back), and
the model/effort/thinking settings. Model defaults to `claude-opus-4-8`; the doc
notes where the firm may opt into a cheaper model for simple extraction.

---

## Worked Example — `Astute-QBO-Books-Health.workflow.json`

A **fully-wired, near-runnable** example of one ingestion→AI node, so the developer
has a concrete pattern to copy for the others. 9 nodes:

1. Manual trigger → **Config** (client name, QBO `realmId`, API base)
2. **QBO: A/R aging**, **A/P aging**, **Balance Sheet** — real QBO API v3 report
   pulls (`/v3/company/{realmId}/reports/...`) via the QuickBooks credential
3. **QBO: recent transactions** — a `SELECT * FROM Purchase` query
4. **Build Claude request** (Code) — assembles the QBO data and builds the
   Anthropic payload with the Books Health prompt + structured-output schema
5. **Claude: Books Health** — real `POST https://api.anthropic.com/v1/messages`
   call via the Anthropic credential
6. **Parse Books Health** (Code) — parses the structured JSON into
   `books_health` for the brief

Verified: JSON valid, all connections resolve, both Code nodes compile, and the
request builder produces a valid Anthropic payload + schema at runtime.

### Setup
1. Import the JSON into Karen's n8n.
2. Select Karen's **Astute QuickBooks** credential on the four QBO nodes and her
   **Astute Anthropic** credential on the Claude node.
3. In **Config**, set the client's QBO `realmId` (and `qbo_base` —
   `https://quickbooks.api.intuit.com` for production, or the sandbox base while
   testing).
4. Run. `Parse Books Health` outputs the `books_health` object that feeds the
   Meeting Brief's Books Health section.

### Pattern to copy
Every other ingestion→AI node follows this same shape: **pull (HTTP) → Build
Claude request (Code, using the matching prompt from `Claude-Prompts.md`) →
Claude (HTTP) → Parse (Code)**. Swap the data source and the prompt/schema; keep
the structure.

### Same caveat
Real endpoints and a real Anthropic call, but not executed against Karen's live
QBO/n8n from the build environment — the developer should do one validation run
and confirm the QuickBooks + Anthropic credential types match the installed n8n
version.
