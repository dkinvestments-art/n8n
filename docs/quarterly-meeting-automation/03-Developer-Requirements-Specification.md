# DEVELOPER REQUIREMENTS SPECIFICATION

## Quarterly Client Meeting Preparation — Automation System

**Version:** 1.0
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
| **NotebookLM** | Research | No direct API | Manual tax research tool |
| **BlueJ Tax** | Tax software | Limited | Specialized tax calculations |

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
    → Send templated document request email to client/bookkeeper

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
3. Branch based on client profile (parallel where possible)
4. Collect all data (auto-pull or request)
5. Process data through AI
6. Generate output documents
7. Notify preparer that meeting prep is ready

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
5. Pull bank feed status (last sync date, uncategorized transaction count)
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

**Process:**
1. Determine recipient: `bookkeeper_email` if available, else `client_email`
2. Generate email from template (see Section 5.2)
3. Send via Gmail API or GoHighLevel API
4. Create Karbon work item: "Awaiting financial documents from [Client]"
5. Set up Google Drive watch on client folder for incoming files

**Output:**
- Email sent confirmation
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
   (or requests them via templated email — see Section 5.2)
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

**Output:**
- Formatted meeting agenda (Google Doc or Slides)
- Saved to client's Google Drive folder

---

### 4.8 Sub-Workflow 7: Task Delegation

**Purpose:** Automatically create tasks for team members when the workflow
identifies work that needs human attention.

**Inputs:**
- Flags from all prior sub-workflows (e.g., "reclassification needed",
  "bank feed out of date", "documents requested from client")

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
```

---

## 6. TESTING REQUIREMENTS

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
- All credential placeholders clearly documented
- Version numbered

### 7.2 Google Sheets Templates
- Tax Estimation Calculator (one per entity type)
- Client Profile Matrix
- Client Scorecard Template
- All formulas documented in a separate tab or comment

### 7.3 Google Docs/Slides Templates
- Meeting Agenda Template
- Client Scorecard Presentation Template
- Variable placeholders clearly marked: `{{CLIENT_NAME}}`, `{{REVENUE}}`, etc.

### 7.4 Documentation
- Setup guide (step-by-step for importing into production n8n)
- API credential requirements list (which APIs, which scopes/permissions)
- Troubleshooting guide (common errors and fixes)
- Workflow architecture diagram (using Mermaid)
- Variable reference (all variables used across workflows)
- Training video walkthrough (15-30 minutes)

---

## 8. ACCEPTANCE CRITERIA

The project is considered complete when:
1. All 8 sub-workflows function correctly against sandbox/synthetic data
2. All 6 test scenarios pass
3. All deliverables listed in Section 7 are received
4. Documentation is complete and accurate
5. Training walkthrough is delivered
6. The Firm successfully imports one workflow into their production n8n
   and runs it with their own credentials (Developer provides support
   via screen share)
7. A 2-week support period follows final delivery for bug fixes

---

*This specification should be reviewed and agreed upon by both parties
before development begins. Changes to scope require written agreement.*
