# DEVELOPER REQUIREMENTS SPECIFICATION

## Quarterly Client Meeting Preparation — Automation System

**Version:** 1.1
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

### 1.3 Key Constraint
**The Developer will never have access to real client data.** All development
and testing must use synthetic/sandbox data. The Firm will connect production
systems and validate with real data after handoff.

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
| **Fathom** | Meeting notes | Yes (API) | Post-meeting transcription and action items |
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
  Profile Matrix and run log (see Section 4.13)

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
```

---

## 4. WORKFLOW SPECIFICATIONS

### 4.1 Master Workflow: Quarterly Meeting Prep Pipeline

**Trigger:** Google Calendar event detected 24-48 hours before an event
containing the keyword "Quarterly" or tagged with a specific label.

**Input:** Client name from the calendar event (used to look up Client Profile)

**Overall Flow:**
1. Calendar trigger fires
2. Look up client profile in Google Sheets
3. Alongside the meeting reminder, auto-send a short pre-meeting client
   questionnaire (3-5 questions, via Google Form or Karbon Client Request):
   major purchases this quarter, entity/life changes, questions for the
   meeting. n8n collects responses and passes them to the agenda generator
   (Sub-Workflow 6)
4. Branch based on client profile (parallel where possible)
5. Collect all data (auto-pull or request)
6. Process data through AI
7. Generate output documents
8. Notify preparer that meeting prep is ready — the notification email
   includes **Approve** / **Request Changes** action links (n8n
   Wait-for-webhook / human-in-the-loop pattern)
9. **Approval gate:** client-facing outputs (agenda copies, payment
   reminder schedules, follow-up emails) are only released after the
   preparer clicks Approve. "Request Changes" routes back for revision.

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

**Output:**
- Karbon work items created
- Client follow-up email draft
- Karbon updated

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
- Summary of rule hits/misses per run (feeds the run log — Section 4.13)

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

### 4.13 Monitoring & Observability Requirements

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
- Meeting Agenda: [LINK]
- Client Scorecard: [LINK]
- Tax Estimation: [LINK]
- [IF APPLICABLE] Entity Comparison: [LINK]

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

All testing (including the v1.1 additions: Sub-Workflows 9-11, approval
gates, questionnaire, payment reminders, and monitoring) fits within the
existing 3-week plan — build in weeks 1-2, testing in week 3.

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
| F | Multi-Entity | QBO (API) | Rippling (manual pay stub upload) | CA | C-Corp with PTE election |

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
- Includes the new workflow JSONs: `QMP-09-Reclassification.json`
  (Sub-Workflow 9), `QMP-10-RulesEngine.json` (Sub-Workflow 10), and
  `QMP-11-PaymentReminders.json` (Sub-Workflow 11)
- All credential placeholders clearly documented
- Version numbered

### 7.2 Google Sheets Templates
- Tax Estimation Calculator (one per entity type)
- Client Profile Matrix
- Client Scorecard Template
- Reclassification Review tab (with Approve checkbox column) + audit log
  tab (Sub-Workflow 9)
- Rules tab for the Virtual Categorization Rules Engine (Sub-Workflow 10)
- Run log sheet (Section 4.13)
- All formulas documented in a separate tab or comment

### 7.3 Google Docs/Slides Templates
- Meeting Agenda Template
- Client Scorecard Presentation Template
- Research Memo Template (cited tax research memo — Blue J + Claude output)
- Variable placeholders clearly marked: `{{CLIENT_NAME}}`, `{{REVENUE}}`, etc.

### 7.4 Documentation
- Setup guide (step-by-step for importing into production n8n)
- Looker Studio dashboard setup instructions (connecting the Client Profile
  Matrix + run log; Section 4.13)
- API credential requirements list (which APIs, which scopes/permissions)
- Troubleshooting guide (common errors and fixes)
- Workflow architecture diagram (using Mermaid)
- Variable reference (all variables used across workflows)
- Training video walkthrough (15-30 minutes)

---

## 8. ACCEPTANCE CRITERIA

The project is considered complete when:
1. All 11 sub-workflows function correctly against sandbox/synthetic data
2. All 6 test scenarios pass
3. All deliverables listed in Section 7 are received
4. Documentation is complete and accurate
5. Training walkthrough is delivered
6. The Firm successfully imports one workflow into their production n8n
   and runs it with their own credentials (Developer provides support
   via screen share)
7. A short support period follows final delivery for bug fixes,
   within the final week of the overall 3-week project timeline

---

*This specification should be reviewed and agreed upon by both parties
before development begins. Changes to scope require written agreement.*
