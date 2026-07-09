# DEVELOPER REQUIREMENTS SPECIFICATION

## Quarterly Client Meeting Preparation — Automation System

**Version:** 2.0
**Date:** _______________
**Prepared by:** _______________
**For:** Third-Party Developer Engagement

---

## 1. EXECUTIVE SUMMARY

### 1.1 Business Context
The Firm provides tax advisory, tax preparation, and financial planning
services to small business clients. Each quarter, the Firm conducts client
review meetings that require significant manual preparation — pulling
financial data from multiple systems, calculating estimated tax payments,
building client scorecards, and preparing meeting agendas.

### 1.2 Project Goal
Build a modular, adaptive automation system using n8n that reduces quarterly
meeting preparation time from approximately 75-90 minutes per client to
15-20 minutes of review-only time, while maintaining full IRS compliance
and supporting clients with varying technology setups.

**v2.0 scope expansion:** the system must ingest ALL current client
intelligence — client communications, the prior meeting transcript, tax
returns and prior tax plans, the full client file folder, books health, and
a quarterly tax strategy screen — and produce a complete **Meeting Brief**
plus a **presentation deck** as the primary deliverables (the plain agenda
of v1.x becomes one section of the brief).

### 1.3 Key Constraint
**The Developer will never have access to real client data.** All development
and testing must use synthetic/sandbox data. The Firm will connect production
systems and validate with real data after handoff.

**Compliance note (v2.0):** all new ingestion introduced in this version
(client emails, tax returns, prior tax plans, meeting transcripts) is
processed exclusively within firm-controlled systems — the Firm's own n8n
instance and the Firm's own AI API accounts. Nothing changes for the
Developer: development and testing use synthetic emails and synthetic tax
returns; the Developer still never touches real data.

---

## 2. CURRENT TECH STACK

The following systems are in use. The Developer should design workflows that
integrate with as many of these as possible.

| System | Category | API Available | Notes |
|--------|----------|---------------|-------|
| **n8n** | Workflow automation | N/A (this is the platform) | Self-hosted or cloud |
| **Google Workspace** | Email, Drive, Docs, Sheets, Slides, Calendar | Yes (OAuth2) | Primary productivity suite |
| **QuickBooks Online** | Accounting | Yes (Intuit API) | Not all clients use QBO; some use Xero, Desktop QB, or nothing |
| **Intuit ProConnect** | Tax preparation | Limited API | Tax returns stay manual |
| **Karbon** | Practice management & task management | Yes (REST API) | Tracks work items, client communications, and team task delegation |
| **Rippling** | Payroll | Manual / offline | Some clients use Rippling; pay stubs are downloaded manually, no API integration |
| **GoHighLevel** | CRM / Marketing | Yes (REST API) | Email templates and client communication |
| **Claude AI** | AI processing | Yes (Anthropic API) | Data parsing, calculations, text generation |
| **ChatGPT** | AI processing | Yes (OpenAI API) | Backup / alternative AI processing |
| **Fathom** | Meeting notes | Yes (API) | Post-meeting transcription and action items; prior-meeting transcripts also feed forward into next-meeting prep (see Sub-Workflow 13) |
| **Gamma** | AI presentation generation | Yes (API) | Already connected by the Firm — optional polished-deck output path (see Sub-Workflow 20) |
| **Scribe** | Process documentation | Limited | Documenting manual procedures |
| **Antigravity** | RPA / browser automation | Varies | Fallback for systems without APIs |
| **NotebookLM** | Research | No direct API | Secondary research tool — used to cross-check Blue J findings |
| **BlueJ Tax** | AI tax research | Limited | **Primary tool for tax strategy research** — purpose-built AI tax research with citations; findings feed the client research memo (see Sub-Workflow 6) |

### 2.1 Optional Software (not required)

The following tools are optional fallbacks/add-ons and are NOT required for
the core system:

- **SaasAnt Transactions** (~$20/mo) — fallback for bulk QBO transaction
  edits if QBO API batch/sparse updates prove insufficient (see
  Sub-Workflow 9)
- **Looker Studio** (free) — monitoring dashboard on top of the Client
  Profile Matrix and run log (see Section 4.22)

---

## 3. CLIENT VARIABILITY MATRIX

Not all clients have the same setup. The system must handle all combinations.

### 3.1 Client Profile Fields
The Developer shall build a **Client Profile Matrix** (Google Sheets) with
the following fields that drive workflow behavior:

```
client_id               - Unique identifier
client_name             - Display name (for internal use)
entity_type             - S-Corp | C-Corp | LLC | Sole Prop | Multi-Entity
state_primary           - Primary state (e.g., CA, NY, TX)
states_additional       - Additional states (comma-separated)
accounting_software     - QBO | Xero | Desktop_QB | Wave | None
accounting_access       - API_Full | API_ReadOnly | Portal_Login | No_Access
payroll_system          - Rippling | Gusto | ADP | Paychex | Other | None (informational only — which payroll software the client uses)
payroll_access          - Manual_Download | No_Access (no API auto-pull; pay stubs are downloaded manually)
payroll_contact_email   - Who to request pay stubs from (informational)
bookkeeper_email        - Who to request financials from (if no API)
client_email            - Primary client email
meeting_cadence         - Quarterly | Monthly | Semi_Annual
google_drive_folder     - Link to client's document folder
gmail_query_alias       - Email search identifier (from/to alias used for the
                          Gmail API fallback search — see Sub-Workflow 12)
drive_tax_folder        - Link to the client's tax documents folder (returns,
                          prior tax plans — see Sub-Workflow 14)
pmt_file_link           - Link to the client's payment (PMT) schedule file
                          (see Sub-Workflow 15)
last_meeting_transcript_link - Link to the prior meeting's Fathom transcript
                          + summary (auto-maintained by the post-meeting
                          workflow, Sub-Workflow 8 — consumed by
                          Sub-Workflow 13)
karbon_client_id        - Karbon identifier (used for both client lookup and work item creation)
karbon_work_template    - Karbon work template to use when creating work items
has_c_corp              - Yes | No (drives entity comparison model)
has_pte_election        - Yes | No (drives PTE tax calculation)
last_meeting_date       - Date of most recent quarterly meeting
notes                   - Free text for special handling
```

### 3.2 Branching Logic
The workflow must branch based on these profile fields:

```
IF accounting_access = "API_Full" OR "API_ReadOnly"
    → Auto-pull financial reports via API
ELSE IF accounting_access = "Portal_Login"
    → Generate manual pull instructions for team
ELSE
    → Create Karbon Client Request for documents (primary — auto-reminders)
    → FALLBACK: send templated document request email (Gmail/GoHighLevel)
       to client/bookkeeper if the client is not set up in Karbon

IF payroll_system = "None"
    → Skip payroll; flag as "distributions only"
       (pull distributions from accounting data / Balance Sheet if available)
ELSE
    → Manual collection: team/admin downloads pay stubs from the client's
       payroll software and uploads them to the client's Google Drive folder
    → Document-intake mechanism (Claude AI) parses the uploaded pay stub PDF
       to extract withholding numbers

IF entity_type = "Multi-Entity" OR has_c_corp = "Yes"
    → Use multi-entity tax calculation template
    → Include entity comparison model
ELSE
    → Use single-entity tax calculation template

IF client communications are available in Karbon
    → Pull email threads since last_meeting_date via Karbon API
       (Sub-Workflow 12, primary path)
ELSE
    → FALLBACK: Gmail API search using gmail_query_alias
       (from/to client email since last_meeting_date)

IF last_meeting_transcript_link is populated
    → Run Last-Meeting Recap (Sub-Workflow 13)
ELSE
    → Note "first automated cycle — no prior transcript on file" in the brief

IF drive_tax_folder is populated
    → Run Tax Document Intelligence (Sub-Workflow 14)
ELSE
    → Flag "tax documents folder not configured" for manual setup

IF pmt_file_link is populated
    → Extract PMT schedule status in the file inventory (Sub-Workflow 15)
ELSE
    → Flag "no PMT schedule file on record" in the brief's Tax Position section
```

---

## 4. WORKFLOW SPECIFICATIONS

### 4.1 Master Workflow: Quarterly Meeting Prep Pipeline

**Trigger:** Google Calendar event detected 48 hours (two days) before the
meeting — an event containing the keyword "Quarterly" or tagged with a
specific label.

**Input:** Client name from the calendar event (used to look up Client Profile)

**Overall Flow:**
1. Calendar trigger fires (48 hours / two days before the meeting)
2. Look up client profile in Google Sheets
3. Alongside the meeting reminder, auto-send a short pre-meeting client
   questionnaire (3-5 questions, via Google Form or Karbon Client Request):
   major purchases this quarter, entity/life changes, questions for the
   meeting. n8n collects responses and passes them to the Meeting Brief
   Compiler / agenda section (Sub-Workflows 6 and 19). In parallel, send
   Karen the 2-minute Preparer Input Prompt (Sub-Workflow 16 — non-blocking)
4. Branch based on client profile
5. Ingestion fan-out — collect all data (parallel where possible):
   - Karbon pending items (Sub-Workflow 1)
   - Financial data (Sub-Workflow 2)
   - Payroll data — manual pay stub collection (Sub-Workflow 3)
   - Client Communications Digest (Sub-Workflow 12)
   - Last-Meeting Recap from prior Fathom transcript (Sub-Workflow 13)
   - Tax Document Intelligence from drive_tax_folder (Sub-Workflow 14)
   - Client File Inventory incl. PMT schedule status (Sub-Workflow 15)
   - QBO Close & Hygiene Report (Sub-Workflow 18)
6. Process data through AI: Tax Estimation Engine (Sub-Workflow 4),
   Client Scorecard (Sub-Workflow 5), Tax Strategy Screener
   (Sub-Workflow 17)
7. Compile all upstream outputs into the **Meeting Brief**
   (Sub-Workflow 19) and generate the **presentation deck**
   (Sub-Workflow 20)
8. Notify preparer that meeting prep is ready — the notification email
   includes **Approve** / **Request Changes** action links (n8n
   Wait-for-webhook / human-in-the-loop pattern)
9. **Approval gate:** client-facing outputs (agenda copies, the
   presentation deck, payment reminder schedules, follow-up emails) are
   only released after the preparer clicks Approve. "Request Changes"
   routes back for revision.

---

### 4.2 Sub-Workflow 1: Karbon Pending Items Pull

**Purpose:** Retrieve all open/pending work items and recent communications
for the client from Karbon.

**Inputs:**
- `karbon_client_id` from Client Profile

**Process:**
1. Authenticate to Karbon API
2. Retrieve all work items for the client where status is not "Complete"
3. Retrieve recent client communications (last 90 days)
4. Filter for actionable items
5. Format as a structured list

**Output:**
- JSON array of pending items with fields: `title`, `status`, `assigned_to`,
  `due_date`, `description`
- Summary text suitable for inclusion in meeting prep document

**Error Handling:**
- If Karbon API is unavailable: log error, continue workflow, flag
  "Karbon data unavailable — check manually"

---

### 4.3 Sub-Workflow 2: Financial Data Collection

**Purpose:** Obtain P&L and Balance Sheet data for the client.

**Branch A: API Available (QBO or Xero)**

**Inputs:**
- `accounting_software` and `accounting_access` from Client Profile
- Date ranges: Current YTD, Prior 12 months, Previous 12 months

**Process (QBO):**
1. Authenticate to QBO API using stored credentials
2. Pull Profit & Loss report — current year to last completed month
3. Pull Profit & Loss report — prior 12 months
4. Pull Balance Sheet — same date ranges
5. Pull bank feed status (last sync date, uncategorized transaction count —
   also feeds the Virtual Categorization Rules Engine, Sub-Workflow 10)
6. If `entity_type` = "Multi-Entity": pull reports by class/location
7. Export data as structured JSON

**Process (Xero):**
1. Authenticate to Xero API
2. Pull equivalent reports using Xero's report endpoints
3. Normalize data format to match QBO output structure

**Output:**
- Structured financial data (JSON)
- Bank feed health status
- Saved CSV/PDF copies to Google Drive client folder

**Branch B: No API Access**

**Process (primary — Karbon Client Request):**
1. Determine recipient: `bookkeeper_email` if available, else `client_email`
2. n8n creates a **Karbon Client Request** via the Karbon API listing the
   documents needed (Karbon's built-in client tasks that automatically
   remind the client until completed)
3. Karbon handles the reminder cadence automatically — no custom
   follow-up emails needed
4. n8n detects completion of the Client Request (polling or webhook) and
   proceeds to document intake
5. Create Karbon work item: "Awaiting financial documents from [Client]"
6. Set up Google Drive watch on client folder for incoming files

**Process (fallback — templated email):**
For clients not set up in Karbon:
1. Generate email from template (see Section 5.1)
2. Send via Gmail API or GoHighLevel API
3. Continue with steps 5-6 above

**Output:**
- Karbon Client Request ID (or email sent confirmation for fallback)
- Karbon work item ID
- Google Drive watch trigger configured

**Branch C: Document Intake (triggered when files arrive)**

**Process:**
1. Google Drive trigger detects new file in client folder
2. Determine file type (CSV, PDF, Excel)
3. If CSV/Excel: parse directly
4. If PDF: send to Claude AI for extraction
5. Normalize data into standard financial data JSON format
6. Continue to scorecard generation

---

### 4.4 Sub-Workflow 3: Payroll Data Collection

**Purpose:** Obtain YTD payroll, withholding, and compensation data for
business owners/employees.

**Note:** Payroll is collected **manually** — the Firm does NOT connect via
API to client payroll systems. The Firm's team (or an admin) downloads the
pay stubs from whatever payroll software the client uses (e.g., Rippling,
Gusto, ADP) and uploads them to the client's Google Drive folder. The
document-intake mechanism then uses Claude AI to parse the uploaded pay stub
PDFs and extract the withholding numbers. Parsing an uploaded stub is fine —
it does NOT count as connecting to a payroll system.

**Branch A: Client Has Payroll (manual pay stub collection)**

**Inputs:**
- `payroll_system` from Client Profile (informational — which software the
  client uses)
- `payroll_contact_email` (who to request stubs from, if needed)
- Employee list (from Client Profile or prior setup)

**Process:**
1. Team/admin manually downloads the YTD pay stubs from the client's payroll
   software and uploads them to the client's Google Drive folder
   (or requests them via a **Karbon Client Request** created by n8n — Karbon
   auto-reminds until completed; templated email per Section 5.2 remains
   the fallback for contacts not set up in Karbon)
2. Google Drive trigger detects the uploaded pay stub PDF(s)
3. Send the pay stub PDF to Claude AI for extraction of: gross pay, federal
   withholding, state withholding, deductions, health insurance premiums
4. Calculate annualized projections (YTD / months elapsed * 12)
5. Format as structured data

**Output:**
- Payroll summary JSON
- Pay stub PDFs retained in Google Drive client folder

**Branch B: No Payroll System**

**Process:**
1. Flag in prep document: "No W-2 payroll. Owner compensation via
   distributions only."
2. Pull distribution data from Balance Sheet (if API available) or
   flag for manual review

**Optional Intake Avenues (not in the critical path — manual collection
remains the default):**

- **Dedicated intake mailbox:** a mailbox such as `payroll@firm` watched by
  n8n. Clients or their payroll contacts email pay stubs in; n8n files the
  attachments to the client's Google Drive folder and parses them
  automatically via the standard document-intake mechanism.
- **QBO Payroll via existing QBO connection:** where a client's payroll runs
  inside QBO Payroll on a QBO account the Firm ALREADY accesses, payslips
  can be pulled through that same existing QBO connection — no new payroll
  dashboard logins and no new API connections to client payroll systems.

Both avenues are optional conveniences only; the manual pay stub
download/upload path is the supported default.

---

### 4.5 Sub-Workflow 4: Tax Estimation Engine

**Purpose:** Calculate estimated quarterly tax payments based on collected
financial and payroll data.

**Inputs:**
- Financial data JSON (from Sub-Workflow 2)
- Payroll data JSON (from Sub-Workflow 3)
- Client Profile (entity type, state, has_c_corp, has_pte_election)

**Process:**
1. Select appropriate Google Sheets tax template based on entity type
2. Populate template with:
   - YTD income / projected annual income
   - YTD expenses / projected annual expenses
   - Owner W-2 compensation and withholdings
   - Prior year tax liability (from Client Profile or manual input)
3. Calculate:
   - **S-Corp pass-through income** (if applicable)
   - **C-Corp taxable income** at 21% federal, 8.84% CA (if applicable)
   - **PTE tax** at 9.3% of qualifying income (if CA PTE election)
   - **Individual estimated tax** (federal + state)
   - **Quarterly payment amounts** using CA schedule (30% / 40% / 0% / 30%)
     and federal schedule (25% / 25% / 25% / 25%)
   - **Total withholdings credit** (from payroll data)
   - **Net estimated payment due** = total tax - withholdings - PTE credits
4. If `has_c_corp` = Yes:
   - Calculate Scenario A: current entity structure
   - Calculate Scenario B: without C-Corp (all income in S-Corp)
   - Calculate tax savings delta
5. Send populated template to Claude AI for validation:
   - "Review these estimated tax calculations. Flag any anomalies,
     unusual ratios, or potential errors. Compare quarterly payment to
     prior year if available."

**Output:**
- Populated Google Sheets tax calculator
- Tax savings comparison (if multi-entity)
- AI validation notes
- Quarterly payment schedule summary

**Templates Needed (Developer creates with formulas, Firm validates):**
- Template A: S-Corp Only (single state)
- Template B: C-Corp Only (single state)
- Template C: S-Corp + C-Corp Multi-Entity
- Template D: Sole Prop / LLC
- Template E: Multi-State Modifier (add-on sheet)

---

### 4.6 Sub-Workflow 5: Client Scorecard Generation

**Purpose:** Generate a four-metric scorecard comparing current performance
to prior period.

**Inputs:**
- Financial data JSON (from Sub-Workflow 2)
- Payroll data JSON (from Sub-Workflow 3)

**Process:**
1. Calculate from financial data:
   - **Revenue**: Last 12 months vs. Prior 12 months ($ and % change)
   - **Gross Profit Margin**: (Revenue - COGS) / Revenue (both periods)
   - **Net Profit Margin**: Net Income / Revenue (both periods)
   - **Owner Take-Home**: W-2 salary + distributions + benefits (both periods)
2. Send to Claude AI with prompt:
   - "Generate a brief narrative (2-3 sentences) explaining the scorecard
     trends. Focus on what drives the changes. If revenue is up but profit
     is down, explain possible causes. If distributions look unusual
     (e.g., shareholder loan reclassification), flag it."
3. Format output for meeting presentation

**Output:**
- Scorecard data (4 metrics, 2 periods each, with % change)
- AI-generated narrative summary
- Formatted for insertion into Google Slides or Google Docs

---

### 4.7 Sub-Workflow 6: Meeting Agenda Generation

**Purpose:** Generate a structured quarterly meeting agenda with talking points.

**Note (v2.0):** the agenda generator is no longer the standalone primary
deliverable — it is now a **component of the Meeting Brief Compiler
(Sub-Workflow 19)**. Its output feeds the brief's agenda-related sections
(Key Talking Points, Questions for the Client, Next 90 Days).

**Inputs:**
- Pending items (from Sub-Workflow 1)
- Tax estimation results (from Sub-Workflow 4)
- Scorecard (from Sub-Workflow 5)
- Client Profile
- Prior meeting notes (if available in Karbon or Google Drive)
- Pre-meeting client questionnaire responses (collected by n8n via the
  master workflow — see Section 4.1): major purchases, entity/life changes,
  client questions for the meeting

**Process:**
1. Compile all inputs into a structured prompt
2. Send to Claude AI with the following instruction:
   ```
   Generate a quarterly client meeting agenda with the following sections:

   1. QUICK WIN — Highlight a specific tax savings or strategic win
      from this quarter. Use actual numbers from the tax estimation.

   2. SCORECARD REVIEW — Summarize the 4 metrics (revenue, profit,
      take-home, tax). Keep it brief — 1-2 sentences per metric.
      Focus on the tax story, not CFO-level analysis.

   3. NEXT 90 DAYS — List 2-3 specific action items or strategies
      to pursue. Base these on the client's entity type, pending items,
      and any open opportunities.

   4. ESTIMATED TAX PAYMENTS — Show exact payment amounts and due dates
      for the upcoming quarter (federal, state, PTE, C-Corp if applicable).

   5. OPEN ITEMS — List any pending items from Karbon that need discussion.

   6. CLIENT QUESTIONS — Leave space for client questions.

   Keep the tone advisory, not technical. The audience is a business owner,
   not an accountant.
   ```
3. Format output into Google Docs or Google Slides template

**Tax Strategy Research Memo (when the agenda surfaces a research question):**
- **Blue J** (already in the Firm's stack) is the primary research tool —
  purpose-built AI tax research with citations
- Blue J findings + Claude AI compose a client-specific, cited research
  memo using the Research Memo Google Docs template (see Section 7.3)
- **NotebookLM** is used for cross-checking the research
- A human (the preparer) validates ALL research conclusions before anything
  is presented to the client

**Output:**
- Formatted meeting agenda (Google Doc or Slides)
- Client-specific cited Research Memo (Google Doc), when applicable
- Saved to client's Google Drive folder

---

### 4.8 Sub-Workflow 7: Task Delegation

**Purpose:** Automatically create tasks for team members when the workflow
identifies work that needs human attention.

**Inputs:**
- Flags from all prior sub-workflows (e.g., "reclassification proposals
  awaiting approval — see Sub-Workflow 9", "bank feed out of date",
  "documents requested from client")

**Process:**
1. For each flag, create a Karbon work item:
   - Title: descriptive action item
   - Assignee: based on task type (admin tasks → designated team member,
     review tasks → preparer)
   - Due date: 2 business days before meeting, or specific deadline
   - Description: context from the workflow that generated the flag
2. Send summary notification to preparer via email or Slack

**Output:**
- Karbon work item IDs
- Notification sent confirmation

---

### 4.9 Sub-Workflow 8: Post-Meeting Action Items (Fathom Integration)

**Purpose:** After the quarterly meeting, automatically extract action items
from the Fathom transcript and create follow-up tasks.

**Trigger:** Fathom webhook or polling for new meeting transcripts

**Process:**
1. Detect new Fathom transcript for the client
2. Send transcript to Claude AI with prompt:
   ```
   Extract all action items from this meeting transcript. For each item:
   - Who is responsible (Firm team member or client)
   - What specifically needs to be done
   - Suggested deadline
   - Priority (high/medium/low)
   ```
3. Create Karbon work items for Firm-owned action items
4. Create follow-up email draft (via Gmail or GoHighLevel) for client-owned
   action items
5. Update Karbon with meeting notes summary
6. Update `last_meeting_transcript_link` (and `last_meeting_date`) in the
   Client Profile Matrix with the new Fathom transcript + summary link —
   this feeds the next quarter's Last-Meeting Recap (Sub-Workflow 13)

**Output:**
- Karbon work items created
- Client follow-up email draft
- Karbon updated
- Client Profile Matrix updated (`last_meeting_transcript_link`,
  `last_meeting_date`)

---

### 4.10 Sub-Workflow 9: Transaction Reclassification (Propose → Approve → Apply)

**Purpose:** Semi-automate mass transaction reclassification in QBO. Instead
of the Firm reclassifying transactions fully by hand, the system proposes
changes, a human approves them, and n8n applies the approved changes.
Human judgment stays in the loop via the approval step.

**Inputs:**
- Target account(s) and date range (from a flag, a Karbon work item, or
  manual trigger)
- The Firm's chart of accounts (pulled via QBO API)
- Rules reference sheet (the "Rules" tab — see Sub-Workflow 10)

**Process:**
1. **Propose:** n8n pulls the target transactions via the QBO API (filtered
   by account and date range)
2. Claude AI proposes a target category/class for each transaction,
   referencing the Firm's chart of accounts and the rules reference sheet
3. Proposals are written to a **"Reclassification Review" tab** in Google
   Sheets: one row per transaction with current category, proposed
   category/class, AI reasoning, and an **Approve checkbox column**
4. **Approve:** a human reviews the tab and ticks the Approve checkbox for
   each change they accept
5. **Apply:** n8n detects approvals (Google Sheets trigger or scheduled
   polling) and applies ONLY the approved changes via QBO API batch/sparse
   updates against the relevant entities (`Purchase`, `Deposit`,
   `JournalEntry`)
6. Every applied change is written to a full **audit log tab** recording:
   transaction ID, old value, new value, who approved, timestamp

**Error Handling:**
- Failed updates are flagged (in the Review tab and via notification) —
  never silently skipped
- Partial batch failures are retried individually, then flagged

**Fallback (if QBO API bulk updates prove insufficient):**
- **SaasAnt Transactions** (~$20/mo, optional) for bulk import/edit, or
- **Antigravity** RPA browser automation

**Output:**
- Updated QBO transactions (approved changes only)
- Populated audit log tab
- Flags for any failed or skipped updates

---

### 4.11 Sub-Workflow 10: Virtual Categorization Rules Engine

**Purpose:** QBO's built-in bank-feed rules are NOT editable via API — so
n8n runs its OWN scheduled rules engine instead of trying to manage QBO's
rules. This removes the need for the Firm to maintain categorization
manually inside QBO.

**Trigger:** Scheduled (e.g., weekly)

**Rule Storage:**
- Rules live in a **"Rules" tab** in Google Sheets
- Each rule defines match conditions (description contains / amount /
  account) → target category/class

**Process:**
1. On schedule, n8n pulls new uncategorized transactions via the QBO API
2. Each transaction is evaluated against the Rules tab; matches are
   categorized via QBO API updates
3. Claude AI monitors recurring uncategorized patterns (transactions that
   repeatedly match no rule) and **suggests new rules**
4. Suggested rules are written to the Rules tab as "pending" — they require
   **human approval before activation**; only approved rules are applied

**Output:**
- Newly categorized transactions in QBO
- Suggested rules pending human approval
- Summary of rule hits/misses per run (feeds the run log — Section 4.22)

---

### 4.12 Sub-Workflow 11: Estimated Payment Reminder Workflow

**Purpose:** After prep approval, make sure the client (and the Firm) never
misses an estimated payment.

**Trigger:** Preparer clicks Approve on the prep-ready notification
(Section 4.1 approval gate)

**Process:**
1. Read the quarterly payment schedule from the Tax Estimation Engine
   output (Sub-Workflow 4): federal and state amounts and due dates
2. n8n schedules reminder emails ahead of each federal and state
   estimated-payment due date, addressed to:
   - The client, and
   - The Firm's internal payments coordinator
3. Each reminder includes the exact payment amount and the relevant payment
   links (EFTPS for federal, CA FTB Web Pay for California, etc.)
4. Reminders are **cancellable/reschedulable** if the estimated amounts
   change (e.g., a revised calculation) — n8n cancels pending reminders and
   re-schedules with updated amounts

**Output:**
- Scheduled reminder emails (with cancellation handles stored in the run
  log)
- Confirmation summary to the payments coordinator

---

### 4.13 Sub-Workflow 12: Client Communications Digest

**Purpose:** Give the preparer a complete picture of everything said between
the Firm and the client since the last meeting.

**Inputs:**
- `karbon_client_id`, `client_email`, `gmail_query_alias`,
  `last_meeting_date` from Client Profile

**Process:**
1. **Primary:** pull client email threads/communications since
   `last_meeting_date` via the Karbon API (Karbon aggregates client emails)
2. **Fallback:** if the client's communications are not available in
   Karbon, run a Gmail API search using `gmail_query_alias`
   (from/to the client's email address since the last meeting)
3. Send the collected threads to Claude AI to produce a digest covering:
   - Commitments the Firm made
   - Commitments the client made
   - Questions asked — answered and unanswered
   - Life/business changes mentioned
   - Unresolved threads
   - Overall sentiment
4. Format both a structured JSON digest and a narrative summary

**Output:**
- Structured digest JSON
- Narrative digest for the Meeting Brief ("Since Last Meeting" section)

**Error Handling:**
- If neither Karbon nor Gmail returns results: flag "no communications
  found since last meeting — verify gmail_query_alias" and continue

---

### 4.14 Sub-Workflow 13: Last-Meeting Recap (Transcript Feed-Forward)

**Purpose:** Feed the prior meeting forward into this one — what was
discussed, what was promised, and what actually happened since.

**Inputs:**
- `last_meeting_transcript_link` from Client Profile (auto-maintained by
  the post-meeting workflow, Sub-Workflow 8)
- Karbon work items for the client (from Sub-Workflow 1)

**Process:**
1. Retrieve the prior meeting's Fathom transcript + summary via the stored
   link
2. Send to Claude AI to extract:
   - Topics discussed
   - Promises made by each side (Firm and client)
   - Strategies discussed but not yet implemented
   - Client questions raised
3. Cross-reference each extracted promise against Karbon work items to
   assign a status: **Done / Pending / Blocked**

**Output:**
- "Since Last Meeting" progress report: recap of promises with
  Done/Pending/Blocked status, plus not-yet-implemented strategies to
  resurface

**Error Handling:**
- If no transcript link exists (first automated cycle): note "no prior
  transcript on file" in the brief and continue

---

### 4.15 Sub-Workflow 14: Tax Document Intelligence

**Purpose:** Extract the client's current tax position from filed returns
and prior tax plans, so the estimator and strategy screener work from real
positions rather than assumptions.

**Inputs:**
- `drive_tax_folder` from Client Profile

**Process:**
1. Scan the client's `drive_tax_folder` for tax returns (federal + state,
   business + personal) and prior tax plans
2. Send documents to Claude AI to extract key data points:
   - AGI and taxable income
   - Marginal and effective tax rates
   - Carryforwards: NOL, capital loss, charitable, credits
   - Elections in effect: S-Corp, PTE, accounting methods
   - Depreciation schedules / asset listings
   - Safe harbor targets (110% of prior-year liability)
   - Estimated payments made to date
3. Assemble a structured **"Tax Position" JSON**

**Output:**
- Tax Position JSON — consumed by the Tax Estimation Engine
  (Sub-Workflow 4) and the Tax Strategy Screener (Sub-Workflow 17)
- Tax Position section content for the Meeting Brief

**Error Handling:**
- Missing or unreadable returns: flag which documents/data points are
  missing; the estimator falls back to Client Profile / manual inputs

---

### 4.16 Sub-Workflow 15: Client File Inventory

**Purpose:** Enumerate and triage ALL files in the client's Google Drive
folder (not just the current quarter) so nothing relevant is missed —
including answering "does Christina know what to pay?"

**Inputs:**
- `google_drive_folder`, `pmt_file_link` from Client Profile

**Process:**
1. Enumerate all files in the client's Google Drive folder: PMT schedule
   file, entity documents, prior scorecards, planning docs, etc.
2. Claude AI triages each file's relevance for THIS meeting (relevant /
   background / stale)
3. Extract **PMT schedule status** from the PMT file: payments scheduled
   vs. made vs. upcoming — so the brief explicitly answers whether the
   client knows what to pay and when

**Output:**
- File inventory with relevance flags
- PMT status summary (feeds the brief's Tax Position section)

**Error Handling:**
- If `pmt_file_link` is missing or the file is unparseable: flag "PMT
  schedule status unknown — check manually"

---

### 4.17 Sub-Workflow 16: Preparer Input Prompt

**Purpose:** Capture the preparer's (Karen's) own knowledge — updates,
concerns, topics — with a 2-minute effort, without blocking the pipeline.

**Trigger:** Fires at master-workflow trigger time (48 hours / two days
before the meeting)

**Process:**
1. Email Karen a short prompt: "Prepping for [CLIENT] on [DATE]. Any
   updates, concerns, or topics to include? Reply to this email or leave
   blank."
2. n8n captures the reply (email parse) and folds the content into the
   Meeting Brief
3. **Non-blocking:** if no reply is received by T-24h, proceed without it
   and note "no preparer input" in the brief

**Output:**
- Preparer input text (or "no preparer input" note) for the Meeting Brief

---

### 4.18 Sub-Workflow 17: Tax Strategy Screener

**Purpose:** The highest-value addition — every quarter, systematically
screen a curated Strategy Library against the client's fresh data and
surface ranked, quantified tax-saving opportunities.

**Rule Storage — the "Strategy Library" (Google Sheet):**
Each row defines one strategy:
- Strategy name and description
- Category (entity / compensation / retirement / real estate / family /
  health / credits / charitable / investment & exit / timing / state)
- Trigger conditions (entity type, income thresholds, real estate
  ownership, children, retirement plan status, state, W-2 comp levels,
  etc.)
- Estimated savings formula / heuristic
- IRC / authority reference (required — a strategy row without authority
  citations is not eligible for screening)
- **Risk rating: Conservative / Moderate / Aggressive** (drives the
  validation workflow below)
- Economic substance / documentation requirements (what the client must
  actually do and keep for the strategy to hold up)
- Added by / date added / review status (Draft → Firm-Approved; only
  Firm-Approved rows are screened against clients)
- Per-client status: implemented / rejected / candidate

**Inputs:**
- QBO financials (Sub-Workflow 2)
- Tax Position JSON (Sub-Workflow 14)
- Client Profile
- Pre-meeting questionnaire answers

**Process:**
1. Each quarter, n8n + Claude AI evaluate EVERY library strategy against
   the client's fresh data
2. Filter out strategies already implemented or previously rejected for
   this client (per-client status column)
3. For each triggered strategy, compute estimated annual savings using the
   library's formula/heuristic
4. Rank the shortlist by estimated savings
5. The top 2-3 candidates get a **Blue J-validated research memo** via the
   existing research flow (see Sub-Workflow 6): Blue J findings + Claude
   compose a cited memo; NotebookLM cross-checks; a human validates before
   anything is client-facing

**Seed Strategy Library (~35 strategies, seeded by the Developer in
Week 2; content curated and extended by the Firm on an ongoing basis):**

*Entity & compensation:*
1. S-Corp reasonable compensation optimization
2. PTE (pass-through entity) election
3. C-Corp / S-Corp restructuring
4. Multi-entity structures (management company / inter-company fee
   arrangements) — Moderate risk
5. Fiscal year election for C-Corp income deferral
6. QSBS (IRC 1202) qualification and stacking
7. Section 1244 stock loss treatment

*Retirement:*
8. Solo 401(k) / SEP optimization
9. Defined benefit / cash balance plan
10. Mega backdoor Roth
11. Backdoor Roth IRA
12. Roth conversion timing (low-income years)

*Real estate:*
13. Cost segregation + bonus depreciation
14. Real estate professional status (REPS)
15. Short-term rental "loophole" (IRC 469, 7-day rule)
16. 1031 exchange
17. Qualified Opportunity Zone investment
18. Augusta rule (IRC 280A(g))
19. Passive activity grouping elections
20. Closely-held C-Corp passive loss offset (IRC 469(e) exception — the
    strategy validated for the insurance agency client)

*Family:*
21. Hiring children
22. Income shifting to lower-bracket family members
23. 529 superfunding (5-year gift election)

*Health & fringe:*
24. Accountable plan / home office
25. HRA / ICHRA
26. HSA maximization
27. Section 105 medical reimbursement plan

*Credits & incentives:*
28. R&D credit
29. Work Opportunity Tax Credit (WOTC)
30. Clean energy credits (179D, solar ITC, EV)

*Charitable:*
31. Charitable bunching / donor-advised fund (DAF)
32. Appreciated stock gifting
33. Charitable remainder / lead trusts (CRT/CLT) — Moderate risk

*Investment & exit:*
34. Installment sale structuring
35. Tax-loss harvesting / direct indexing
36. Income timing / shifting across years

**Library Extensibility — Custom & Creative Strategies:**
The library is designed to grow. Four intake paths, all landing as
**Draft** rows that require Firm approval before they screen against any
client:

1. **Manual add** — anyone at the Firm adds a row anytime; the sheet is
   the single source of truth. A row template with data-validation
   dropdowns keeps entries consistent.
2. **AI strategy discovery** — during each screening run, Claude is also
   prompted: "given this client's full fact pattern, are there tax-saving
   opportunities NOT in the library?" Any suggestion is written to a
   "Proposed Strategies" tab as Draft, never shown to a client directly.
3. **Transcript mining** — the post-meeting workflow (Sub-Workflow 8)
   flags any strategy discussed in a meeting that isn't in the library
   and proposes a Draft row (this captures the Firm's own creative ideas
   the moment they surface on calls).
4. **Quarterly law-change sweep** — a scheduled n8n job has Claude + Blue J
   review recent federal/state tax law changes and propose new or updated
   Draft rows (new credits, expiring provisions, threshold changes).

**Guardrails for custom/creative strategies:**
- Draft rows never screen against clients — only Firm-Approved rows do
- Every row must carry authority citations and economic substance notes
- **Aggressive-rated strategies always require a Blue J-validated research
  memo AND explicit preparer sign-off before appearing in any brief** —
  they are never auto-included on screener output alone
- Strategies resembling listed transactions or reportable transactions
  under IRS Notice guidance (e.g., syndicated conservation easements,
  abusive micro-captives) are excluded by policy — the intake template
  includes a checklist question forcing this review
- The screener's output language distinguishes risk tiers so the client
  conversation is framed honestly

**Output:**
- Ranked shortlist of triggered strategies with estimated annual savings
- Research memo links for the top 2-3 candidates
- Feeds the brief's Strategy Opportunities section (Sub-Workflow 19)

---

### 4.19 Sub-Workflow 18: QBO Close & Hygiene Report

**Purpose:** Give the preparer an honest "Books Health" picture — is the
month closed, what's uncategorized, what's stale — before walking into the
meeting.

**Inputs:**
- QBO API connection (per `accounting_access`)

**Process:**
1. Pull from the QBO API:
   - Full uncategorized/unreviewed transaction list (also feeds the
     existing reclassification engine, Sub-Workflow 9, and rules engine,
     Sub-Workflow 10)
   - Last reconciliation date per bank/credit account
   - Bank feed sync lag
   - A/R aging summary
   - A/P aging summary
   - Anomalies: negative balances, large one-off transactions
2. Claude AI proposes categorizations for outstanding uncategorized items
   (approval flows through Sub-Workflow 9 — propose → approve → apply)

**Output:**
- "Books Health" section for the Meeting Brief: month-end close status
  checklist + outstanding items with AI-proposed categorizations

**Error Handling:**
- No QBO access (Branch B clients): section reads "books health not
  available — no accounting API access"

---

### 4.20 Sub-Workflow 19: Meeting Brief Compiler

**Purpose:** The primary deliverable of v2.0 — compile ALL upstream outputs
into ONE Google Doc "Meeting Brief" (replaces the plain agenda as the
primary deliverable; the agenda generator, Sub-Workflow 6, is now a
component of this compiler).

**Inputs:** outputs of Sub-Workflows 1-6, 12-18, questionnaire responses,
and preparer input (Sub-Workflow 16)

**Process:**
Compile a Google Doc from the Meeting Brief template with these sections:
1. **Executive Summary** (5 bullets)
2. **Since Last Meeting** — email digest (SW12) + completed work + recap
   of promises with Done/Pending/Blocked status (SW13)
3. **Follow-Up Items** — consolidated, with owners
4. **Financial Review** — scorecard, trends, CFO talking points (cash
   position, margins, A/R-A/P), framed within the tax story per the Firm's
   advisory positioning
5. **Books Health** — close items, uncategorized transactions,
   reconciliation status (SW18)
6. **Tax Position** — YTD estimates, safe harbor status, PMT schedule
   status (SW4, SW14, SW15)
7. **Strategy Opportunities** — screener results with estimated savings +
   research memo links (SW17)
8. **Key Talking Points** — 7-10, ordered by importance
9. **Questions for the Client**

**Output:**
- Completed Meeting Brief (Google Doc), saved to the client's Google Drive
  folder and linked in the prep-ready notification (Section 5.3)
- Structured brief content passed to the Presentation Deck Generator
  (Sub-Workflow 20)

---

### 4.21 Sub-Workflow 20: Presentation Deck Generator

**Purpose:** Turn the Meeting Brief into a client-facing presentation deck.

**Inputs:**
- Meeting Brief content (Sub-Workflow 19)

**Process (default — Google Slides):**
1. Auto-fill a Google Slides template from the Meeting Brief:
   - Title slide
   - Scorecard visual
   - Since-last-meeting wins
   - Tax position + payments due
   - Strategy opportunities
   - Next 90 days
2. Save the deck to the client's Google Drive folder

**Optional enhancement — Gamma API:**
- The Firm has Gamma connected; as an optional nicer-output path, generate
  a polished deck from the brief content via a Gamma API call
- Google Slides remains the supported default

**Approval:**
- The deck is client-facing and is released ONLY after the existing
  approval gate (Section 4.1, step 9)

**Output:**
- Presentation deck (Google Slides; optionally Gamma), held behind the
  approval gate

---

### 4.22 Monitoring & Observability Requirements

The Developer shall implement:

1. **Run log (Google Sheet):** one row per workflow execution recording:
   client, timestamp, status (success / partial / failed), and any flags
   raised
2. **Looker Studio dashboard (free):** built on top of the Client Profile
   Matrix + run log, showing prep status per client, missing documents,
   and upcoming meetings
3. **Error alert emails:** sent to the Firm immediately on any workflow
   failure (n8n error workflow)
4. **Weekly digest email:** summary of runs, failures, pending approvals,
   outstanding document requests, and upcoming estimated-payment reminders

---

## 5. EMAIL TEMPLATES

### 5.1 Financial Document Request

```
Subject: Quarterly Review Prep — Documents Needed by [DATE]

Hi [CLIENT_NAME],

We're preparing for your upcoming quarterly review on [MEETING_DATE].

To make the most of our time together, could you please provide the
following by [DUE_DATE]:

- Profit & Loss statement (January 1 - [LAST_MONTH_END], [YEAR])
- Balance Sheet as of [LAST_MONTH_END], [YEAR]
- [IF APPLICABLE] Most recent pay stubs for all owners

You can upload these directly to your secure folder here: [DRIVE_LINK]

If your bookkeeper handles these reports, feel free to forward this
email to them.

Looking forward to our meeting!

Best,
[FIRM_NAME]
```

### 5.2 Payroll Data Request

```
Subject: Payroll Information Needed for Quarterly Review

Hi [PAYROLL_CONTACT],

We're preparing [CLIENT_NAME]'s quarterly review and need the following
payroll information for Q[QUARTER] [YEAR]:

- YTD pay stubs for: [OWNER_NAMES]
- YTD payroll summary showing gross pay, federal withholding,
  and state withholding

Please upload to: [DRIVE_LINK]

Needed by: [DUE_DATE]

Thank you!

[FIRM_NAME]
```

### 5.3 Meeting Prep Complete Notification (Internal)

```
Subject: ✓ Quarterly Prep Ready — [CLIENT_NAME] ([MEETING_DATE])

Quarterly meeting prep for [CLIENT_NAME] is ready for your review.

Documents prepared:
- Meeting Brief: [LINK]
- Presentation Deck: [LINK]
- Meeting Agenda (brief section): [LINK]
- Client Scorecard: [LINK]
- Tax Estimation: [LINK]
- [IF APPLICABLE] Entity Comparison: [LINK]
- [IF APPLICABLE] Strategy Research Memos: [LINKS]

Items needing attention:
- [LIST OF FLAGS/ISSUES]

Outstanding document requests:
- [LIST OF PENDING REQUESTS]

Meeting is scheduled for: [MEETING_DATE] at [TIME]

▶ APPROVE PREP: [APPROVE_LINK]
▶ REQUEST CHANGES: [REQUEST_CHANGES_LINK]

Note: client-facing outputs (agenda copies, payment reminder schedules,
follow-up emails) will only be released after you click Approve.
```

The Approve / Request Changes links use n8n's Wait-for-webhook
(human-in-the-loop) pattern: the workflow pauses until a link is clicked,
then either releases client-facing outputs or routes back for revision.

---

## 6. TESTING REQUIREMENTS

All testing (including the v2.0 additions: Sub-Workflows 12-20, plus the
v1.1 additions — Sub-Workflows 9-11, approval gates, questionnaire, payment
reminders, and monitoring) fits within the existing **3-week plan**:

- **Week 1:** core build + the new ingestion workflows (Sub-Workflows
  12-15: communications digest, last-meeting recap, tax document
  intelligence, file inventory)
- **Week 2:** preparer prompt, strategy screener, brief compiler, and deck
  generator (Sub-Workflows 16-20). The Strategy Library content is seeded
  in Week 2 (Developer) and curated by the Firm on an ongoing basis
- **Week 3:** testing (and the support period per Section 8)

### 6.1 Synthetic Test Scenarios
The Developer shall create and test with the following synthetic client
profiles:

| Scenario | Entity | Accounting | Payroll | State | Special |
|----------|--------|-----------|---------|-------|---------|
| A | S-Corp | QBO (API) | Rippling (manual pay stub upload) | CA | Standard case |
| B | C-Corp + S-Corp | QBO (API) | Gusto (manual pay stub upload) | CA | Multi-entity comparison |
| C | LLC | Xero (API) | None | NY | No payroll, distributions only |
| D | Sole Prop | No software | No payroll | TX | Everything manual/email |
| E | S-Corp | QBO (view-only) | ADP (manual pay stub upload) | CA + NY | Multi-state, partial access |
| F | Multi-Entity | QBO (API) | Rippling (manual pay stub upload) | CA | C-Corp with PTE election; real estate ownership + high income (screener trigger test) |

For v2.0, each synthetic client profile is extended with a **synthetic
intelligence corpus**: synthetic email threads (Karbon/Gmail), a synthetic
prior-meeting Fathom transcript, synthetic federal + state tax returns and
a prior tax plan in `drive_tax_folder`, and a synthetic PMT schedule file.
The Developer never touches real emails, returns, or transcripts.

### 6.2 Test Cases
For each scenario, verify:
- [ ] Correct branching logic fires
- [ ] API calls return expected data (sandbox)
- [ ] Email templates generate correctly with proper variable substitution
- [ ] Karbon work items create with correct assignees and due dates
- [ ] Google Sheets templates populate correctly
- [ ] Claude AI prompts return usable responses
- [ ] Google Docs/Slides output is properly formatted
- [ ] Error handling works (API timeout, missing data, malformed response)
- [ ] Google Drive folder structure is created correctly
- [ ] Notification emails send to correct recipients
- [ ] Reclassification propose → approve → apply cycle works: proposals
      written to the Reclassification Review tab, only approved rows are
      applied via QBO API, audit log records old/new values, approver, and
      timestamp; failed updates are flagged, never silently skipped
- [ ] Virtual rules engine categorizes matching uncategorized transactions;
      AI-suggested rules remain inactive until human approval
- [ ] Approval gates work: prep-ready email contains working
      Approve / Request Changes links; client-facing outputs are held until
      Approve is clicked; Request Changes routes back for revision
- [ ] Pre-meeting questionnaire is sent, responses are ingested, and
      questionnaire content appears as input to the agenda generator
- [ ] Estimated payment reminders schedule after approval with correct
      amounts, due dates, and payment links (EFTPS, CA FTB Web Pay), and
      are cancellable when amounts change
- [ ] Email digest (SW12): Karbon-primary pull works; Gmail fallback via
      gmail_query_alias fires when Karbon has no communications; digest
      correctly identifies commitments, unanswered questions, and life/
      business changes seeded in the synthetic threads
- [ ] Transcript feed-forward (SW13): promises seeded in the synthetic
      transcript are extracted and cross-referenced against Karbon work
      items into correct Done / Pending / Blocked statuses
- [ ] Tax return extraction (SW14): AGI, taxable income, rates,
      carryforwards, elections, safe harbor targets, and estimated payments
      made are extracted correctly from the synthetic returns into the Tax
      Position JSON
- [ ] Strategy screener trigger logic (SW17): synthetic client with real
      estate ownership + high income (Scenario F) triggers cost segregation
      and REPS as candidates; already-implemented and previously-rejected
      strategies are filtered out; savings estimates and ranking are
      produced
- [ ] PMT file status (SW15): payments scheduled vs. made vs. upcoming are
      correctly extracted from the synthetic PMT schedule file and surfaced
      in the brief's Tax Position section
- [ ] Preparer input prompt (SW16): reply is captured and folded into the
      brief; with no reply by T-24h the pipeline proceeds and notes "no
      preparer input"
- [ ] Brief compilation (SW19): the Meeting Brief contains all nine
      sections, each populated from the correct upstream sub-workflow, with
      graceful "not available" notes for missing inputs
- [ ] Deck generation (SW20): Google Slides template auto-fills from the
      brief; deck is held until Approve is clicked; optional Gamma path
      documented (and tested if the sandbox has Gamma access)

### 6.3 Performance Requirements
- Full workflow completion (API path): under 3 minutes
- Individual API calls: under 30 seconds with retry
- Claude AI processing: under 60 seconds per prompt
- Total workflow should handle up to 20 clients triggered on the same day

---

## 7. DELIVERABLE SPECIFICATIONS

### 7.1 n8n Workflow Files
- Exported as JSON from the Developer's n8n instance
- Each sub-workflow as a separate file for modularity
- Master workflow that orchestrates sub-workflows
- Clear naming convention: `QMP-01-Master.json`, `QMP-02-Karbon.json`, etc.
- Includes the v1.1 workflow JSONs: `QMP-09-Reclassification.json`
  (Sub-Workflow 9), `QMP-10-RulesEngine.json` (Sub-Workflow 10), and
  `QMP-11-PaymentReminders.json` (Sub-Workflow 11)
- Includes the v2.0 workflow JSONs: `QMP-12-CommsDigest.json`,
  `QMP-13-MeetingRecap.json`, `QMP-14-TaxDocIntelligence.json`,
  `QMP-15-FileInventory.json`, `QMP-16-PreparerPrompt.json`,
  `QMP-17-StrategyScreener.json`, `QMP-18-BooksHealth.json`,
  `QMP-19-BriefCompiler.json`, `QMP-20-DeckGenerator.json`
  (Sub-Workflows 12-20)
- All credential placeholders clearly documented
- Version numbered

### 7.2 Google Sheets Templates
- Tax Estimation Calculator (one per entity type)
- Client Profile Matrix
- Client Scorecard Template
- Reclassification Review tab (with Approve checkbox column) + audit log
  tab (Sub-Workflow 9)
- Rules tab for the Virtual Categorization Rules Engine (Sub-Workflow 10)
- **Strategy Library sheet** (Sub-Workflow 17), seeded with the ~35
  strategies listed in Section 4.18, including trigger conditions, savings
  heuristics, authority references, and per-client status columns
- Run log sheet (Section 4.22)
- All formulas documented in a separate tab or comment

### 7.3 Google Docs/Slides Templates
- **Meeting Brief Template** (Google Doc — the nine-section brief,
  Sub-Workflow 19)
- **Presentation Deck Template** (Google Slides — Sub-Workflow 20)
- Meeting Agenda Template (now populated as sections of the Meeting Brief)
- Client Scorecard Presentation Template
- Research Memo Template (cited tax research memo — Blue J + Claude output)
- Variable placeholders clearly marked: `{{CLIENT_NAME}}`, `{{REVENUE}}`, etc.

### 7.4 Documentation
- Setup guide (step-by-step for importing into production n8n)
- Looker Studio dashboard setup instructions (connecting the Client Profile
  Matrix + run log; Section 4.22)
- API credential requirements list (which APIs, which scopes/permissions)
- Troubleshooting guide (common errors and fixes)
- Workflow architecture diagram (using Mermaid)
- **Tax Position extraction prompt documentation** (the Claude prompts used
  by Sub-Workflow 14 to extract the Tax Position JSON from returns, with
  the expected JSON schema)
- Variable reference (all variables used across workflows)
- Training video walkthrough (15-30 minutes)

---

## 8. ACCEPTANCE CRITERIA

The project is considered complete when:
1. All 20 sub-workflows function correctly against sandbox/synthetic data
2. All 6 test scenarios pass
3. **Brief completeness:** for each synthetic test client, the generated
   Meeting Brief contains all nine sections, each populated from the
   correct upstream sub-workflow (with explicit "not available" notes
   where an input is legitimately missing)
4. **Strategy screener accuracy:** against the synthetic test clients, the
   screener triggers the expected candidate strategies (e.g., cost
   segregation + REPS for the real-estate/high-income client), filters
   out implemented/rejected strategies, and produces ranked savings
   estimates
5. All deliverables listed in Section 7 are received (including the seeded
   Strategy Library sheet and the Meeting Brief + Deck templates)
6. Documentation is complete and accurate
7. Training walkthrough is delivered
8. The Firm successfully imports one workflow into their production n8n
   and runs it with their own credentials (Developer provides support
   via screen share)
9. A short support period follows final delivery for bug fixes,
   within the final week of the overall 3-week project timeline

---

*This specification should be reviewed and agreed upon by both parties
before development begins. Changes to scope require written agreement.*
