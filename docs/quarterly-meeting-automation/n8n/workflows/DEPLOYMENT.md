# QMP Deployment Guide — Full App

Everything needed to stand up the Quarterly Meeting Prep system in **Karen's
Astute Advisors n8n**. Per `../../DATA-GOVERNANCE.md`, every credential is an
Astute account and every artifact lands on Astute infrastructure.

## What's in this folder

| File | Workflow | Trigger |
|------|----------|---------|
| `QMP-00b-Seed-Operations-Sheet.workflow.json` | Creates the **QMP Operations** spreadsheet (9 tabs w/ headers) | Manual, once |
| `QMP-01-Karbon-Work-Items.workflow.json` | Karbon open + completed-since-last-meeting items | Called by master |
| `QMP-02-Financial-Data.workflow.json` | QBO P&L ×3 periods + Balance Sheet | Called by master |
| `QMP-03-Payroll-Parse.workflow.json` | Newest manually-uploaded pay stubs → Claude withholding extract | Called by master |
| `QMP-04-Tax-Estimate.workflow.json` | Quarterly estimates + with/without C-corp comparison | Called by master |
| `QMP-05-Client-Scorecard.workflow.json` | 4-metric scorecard + tax-story narrative | Called by master |
| `QMP-08-Post-Meeting.workflow.json` | Fathom → actions → Karbon, Meeting History, strategy intake, profile update, follow-up draft | Every 2h |
| `QMP-09a-Reclass-Propose.workflow.json` | QBO uncategorized → Claude proposals → Review tab | Weekly Mon 6am |
| `QMP-09b-Reclass-Apply.workflow.json` | Human-approved rows → QBO update + audit log | Manual |
| `QMP-10-Virtual-Rules-Engine.workflow.json` | Firm rules → QBO auto-categorization; unmatched → Proposed Rules | Weekly Mon 7am |
| `QMP-11-Payment-Reminders.workflow.json` | Payment Schedule tab → client reminder emails | Daily 8am |
| `QMP-12-Comms-Digest.workflow.json` | Client emails since last meeting → digest | Called by master |
| `QMP-13-Last-Meeting-Recap.workflow.json` | Meeting History + Karbon → promises Done/Pending/Blocked | Called by master |
| `QMP-14-Tax-Document-Intelligence.workflow.json` | Tax-folder PDFs → tax position extract | Called by master |
| `QMP-15-File-Inventory.workflow.json` | Full client folder + PMT schedule status | Called by master |
| `QMP-16-Preparer-Input-Capture.workflow.json` | "Prep input:" replies → Preparer Notes tab | Gmail poll hourly |
| `QMP-17-Strategy-Screener.workflow.json` | Firm-Approved library × client data → ranked candidates | Called by master |
| `QMP-18-Books-Health-Sub.workflow.json` | A/R + A/P aging + transactions → Books Health | Called by master |
| `QMP-19-Meeting-Brief.workflow.json` | 9-section brief → Google Doc in briefs folder | Called by master |
| `QMP-20-Presentation-Deck.workflow.json` | Copies deck template, fills placeholders via Slides API | Called by master (post-approval) |
| `QMP-MASTER-Orchestrator.workflow.json` | The whole pipeline + approval gate | Every 6h |

Regenerate any file by editing `qmp_lib.py` / `build_sub_workflows.py` /
`build_ops_workflows.py` and re-running the builders. `node validate.js`
re-checks everything (all 21 currently pass).

## Deployment steps

### 1. Credentials (create once in Karen's n8n, all Astute accounts)

| Credential type | Name suggestion | Used by |
|---|---|---|
| Google OAuth2 (Sheets, Docs, Drive, Calendar, Gmail, Slides) | "Karen Astute Advisors Google …" | Most workflows |
| QuickBooks Online OAuth2 | "Karen Astute Advisors QuickBooks" | 02, 09a/b, 10, 18 |
| Anthropic API | "Karen Astute Advisors Anthropic" | All AI nodes |
| HTTP Header Auth (Karbon) | "Karen Astute Advisors Karbon" — headers per Karbon docs (`Authorization: Bearer <token>` + `AccessKey`) | 01, 08, master |
| HTTP Header Auth (Fathom) | "Karen Astute Advisors Fathom" — `X-Api-Key` | 08 |

Every imported node shows a `REPLACE_ASTUTE_*` placeholder — select the real
credential on each node (n8n remembers per credential type, so this is quick).

### 2. Seed the data layer (order matters)

1. Run **Astute-Seed-Automation-Sheets** (in `../`) → creates Strategy Library,
   Client Strategy Status, Client Profile Matrix. Record the three sheet IDs.
2. Import + run **QMP-00b** → creates the **QMP Operations** sheet (Run Log,
   Meeting History, Preparer Notes, Payment Schedule, Reclassification Review,
   Reclass Audit Log, Rules, Proposed Rules, Proposed Strategies). Record its ID.
3. Add these columns to the Client Profile Matrix if not present:
   **`qbo_realm_id`** (the client's QBO company/realm id — required for all QBO
   pulls) and confirm `gmail_query_alias`, `drive_tax_folder`, `pmt_file_link`,
   `last_meeting_transcript_link` exist (v2.0 spec fields).
4. Karen reviews the Strategy Library and flips rows to **Firm-Approved**
   (the screener ignores everything else).

### 3. Paste the shared IDs

Find-and-replace across the imported workflows (or edit the JSONs before
import — plain text):

| Placeholder | Value |
|---|---|
| `PASTE_CLIENT_PROFILE_MATRIX_SHEET_ID` | from step 2.1 |
| `PASTE_TAX_STRATEGY_LIBRARY_SHEET_ID` | from step 2.1 |
| `PASTE_CLIENT_STRATEGY_STATUS_SHEET_ID` | from step 2.1 |
| `PASTE_QMP_OPERATIONS_SHEET_ID` | from step 2.2 |
| `PASTE_KAREN_EMAIL` | Karen's Astute email |
| `PASTE_CHRISTINA_EMAIL` | payments coordinator email |
| `PASTE_ASTUTE_BRIEFS_FOLDER_ID` | Drive folder for generated briefs |
| `PASTE_DECK_TEMPLATE_PRESENTATION_ID` | see deck template below |

Profile-sheet tab name: the workflows read tab **`Sheet1`** on the Client
Profile Matrix — rename accordingly or adjust the nodes.

### 4. Deck template

Create one Google Slides deck ("QMP Deck Template") with these placeholders in
text boxes; QMP-20 replaces them verbatim:
`{{CLIENT_NAME}}`, `{{MEETING_DATE}}`, `{{EXEC_SUMMARY}}`, `{{REVENUE}}`,
`{{REVENUE_CHANGE}}`, `{{TAKE_HOME}}`, `{{NET_MARGIN}}`, `{{TAX_SAVINGS}}`,
`{{Q_FED}}`, `{{Q_STATE}}`, `{{Q_DUE}}`, `{{STRATEGIES}}`, `{{NEXT_90}}`.

### 5. Import order + wiring the master

1. Import all sub-workflows first (01, 02, 03, 04, 05, 12, 13, 14, 15, 17, 18, 19, 20).
2. Import the ops workflows (08, 09a, 09b, 10, 11, 16) and activate their triggers.
3. Import **QMP-MASTER** last. Open each **Run:** node and select the matching
   sub-workflow from the dropdown (n8n assigns IDs at import, so this manual
   selection is required once). The node names tell you which one.
4. Activate the master.

### 6. Validation run (one client)

1. Fill one real client row in the Profile Matrix (with `qbo_realm_id`,
   Karbon key, folders).
2. Create a calendar event "Quarterly — <client name>" ~48h out.
3. Wait for the 6h tick (or run the master manually). Follow the execution:
   every Run node should go green; Karen gets the approve email; clicking
   Approve produces the deck, payment schedule rows, Karbon work item, and a
   Run Log row.
4. Reply to the "Prep input:" email before the run to test preparer notes.

## Operational notes

- **One client per master tick.** If several quarterly meetings land in the
  same window, the master processes one and picks up the next on the following
  6-hour tick (Run Log dedupe prevents repeats).
- **Re-running a prep**: delete that client+meeting's Run Log row, then re-run.
- **"Changes requested"** logs the status and stops; edit the brief doc
  directly, or delete the Run Log row to regenerate from scratch.
- **Reclassification is two-step by design**: 09a proposes into the Review tab;
  a human sets `approved=TRUE`; 09b applies and audits. Nothing touches QBO
  without a human mark.
- **Rules engine**: fill the Rules tab (`contains` match on payee/memo,
  `target_account_id` from QBO chart of accounts, `active=TRUE`). Client-blank
  rules apply to all clients.
- **Strategy intake**: transcript-mined proposals land in Proposed Strategies
  (ops sheet); promote them by adding a row to the Strategy Library and marking
  it Firm-Approved.

## Honest caveats (read before production)

Everything here is structurally validated (JSON, connections, Code-node
compilation, runtime payload checks — `node validate.js`), but **not executed
against live systems** from the build environment. Expect to touch:

1. **Karbon and Fathom API shapes** — endpoints and field names are wired from
   their public docs (`/v3/WorkItems`, OData filters; `/external/v1/meetings`);
   verify against the live APIs, especially response field casing in the
   Format/Match Code nodes.
2. **n8n node parameter drift** — Google Docs update-action shape, Sheets
   update-by-row_number matching, Gmail draft fields, and Calendar options can
   shift between n8n versions. Each is standard; fix-ups are per-node, not
   structural.
3. **QBO transaction coverage** — reclassification currently handles
   `Purchase` transactions (the common case for uncategorized expenses); extend
   the query + mutate nodes for Deposits/JournalEntries when needed.
4. **Gmail `resumeUrl` links** — approval links use n8n's Wait-node resume URL;
   confirm your n8n instance URL is externally reachable for Karen's click.
