# COMPREHENSIVE WORKFLOW DOCUMENTATION

## Quarterly Client Meeting Preparation — Automation System

**Version:** 2.0
**Date:** _______________

---

## TABLE OF CONTENTS

1. [Process Overview](#1-process-overview)
2. [Current Manual Process](#2-current-manual-process)
3. [Automated Process Design](#3-automated-process-design)
4. [Master Workflow Architecture](#4-master-workflow-architecture)
5. [Sub-Workflow Details](#5-sub-workflow-details)
6. [Client Profile Adaptive System](#6-client-profile-adaptive-system)
7. [Tax Estimation Engine](#7-tax-estimation-engine)
8. [Scorecard and Meeting Output](#8-scorecard-and-meeting-output)
9. [Post-Meeting Automation](#9-post-meeting-automation)
10. [Error Handling and Edge Cases](#10-error-handling-and-edge-cases)
11. [Automation Classification](#11-automation-classification)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [Software Integration Map](#13-software-integration-map)
14. [Appendix: Mermaid Diagrams](#14-appendix)

---

## 1. PROCESS OVERVIEW

### 1.1 What This System Does

This automation system prepares all materials needed for quarterly client
review meetings in a tax advisory practice. It replaces approximately
75-90 minutes of manual preparation per client with an automated pipeline
that collects data, performs calculations, and generates meeting-ready
documents.

**New in v2.0 — full client intelligence.** The system now ingests ALL
current client intelligence — email threads since the last meeting, the
prior meeting's transcript, the client's tax returns on Drive, the full
client file inventory, live books data, and the preparer's own input —
and produces a complete **Meeting Brief** (a single 9-section Google Doc)
plus a **presentation deck**. A Tax Strategy Screener evaluates a library
of ~35 tax strategies (extensible with custom strategies) against fresh client data every quarter and ranks
the opportunities by estimated savings. The pipeline fires **48 hours
(two days) before the meeting**.

### 1.2 End-to-End Flow Summary

```mermaid
flowchart LR
    A[Calendar<br/>Trigger] --> B[Collect<br/>Data]
    B --> C[Process &<br/>Calculate]
    C --> D[Generate<br/>Documents]
    D --> E[Notify<br/>Preparer]
    E --> F[Human<br/>Review]
    F --> G[Client<br/>Meeting]
    G --> H[Post-Meeting<br/>Actions]

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#FF9800,color:#fff
    style D fill:#9C27B0,color:#fff
    style E fill:#607D8B,color:#fff
    style F fill:#F44336,color:#fff
    style G fill:#F44336,color:#fff
    style H fill:#4CAF50,color:#fff
```

**Legend:**
- Green = Fully automated
- Blue = Automated with branching logic
- Orange = AI-assisted processing
- Purple = Automated document generation
- Red = Human-required steps

---

## 2. CURRENT MANUAL PROCESS

### 2.1 Process Steps (As Observed from Karen's Walkthrough)

The following 14 steps were identified from the transcript of Karen preparing
for a quarterly meeting with client "Candace":

```mermaid
flowchart TD
    S1[1. Open Karbon<br/>Review pending items<br/>⏱ 5 min] --> S2[2. Download pay stubs<br/>from payroll software<br/>Manual<br/>⏱ 5 min]
    S2 --> S3[3. Create folders in Drive<br/>File payroll docs<br/>⏱ 3 min]
    S3 --> S4[4. Open QBO<br/>Check bank feeds<br/>⏱ 5 min]
    S4 --> S5[5. Fix QBO rules<br/>Edit categorization<br/>⏱ 5 min]
    S5 --> S6[6. Mass reclassify<br/>transactions<br/>⏱ 10 min]
    S6 --> S7[7. Download P&L<br/>and Balance Sheet<br/>⏱ 5 min]
    S7 --> S8[8. Copy tax return<br/>Model estimated taxes<br/>⏱ 15 min]
    S8 --> S9[9. Enter W-2 withholding<br/>from pay stubs<br/>⏱ 5 min]
    S9 --> S10[10. Model entity<br/>tax savings<br/>⏱ 10 min]
    S10 --> S11[11. Research tax<br/>strategies<br/>⏱ 15 min]
    S11 --> S12[12. Build client<br/>scorecard<br/>⏱ 10 min]
    S12 --> S13[13. Write meeting<br/>agenda<br/>⏱ 5 min]
    S13 --> S14[14. Delegate tasks<br/>to team<br/>⏱ 3 min]

    style S1 fill:#4CAF50,color:#fff
    style S2 fill:#F44336,color:#fff
    style S3 fill:#4CAF50,color:#fff
    style S4 fill:#2196F3,color:#fff
    style S5 fill:#FF9800,color:#fff
    style S6 fill:#FF9800,color:#fff
    style S7 fill:#4CAF50,color:#fff
    style S8 fill:#FF9800,color:#fff
    style S9 fill:#FF9800,color:#fff
    style S10 fill:#FF9800,color:#fff
    style S11 fill:#FF9800,color:#fff
    style S12 fill:#FF9800,color:#fff
    style S13 fill:#FF9800,color:#fff
    style S14 fill:#4CAF50,color:#fff
```

**Color legend for current process:**
- Green = Can be fully automated
- Blue = Can be partially automated (detection, not resolution)
- Orange = Can be AI-assisted (human review required)
- Red = Manual by firm choice (payroll pay stubs are collected manually — no payroll dashboard connections)

### 2.2 Time Breakdown

| Step | Current Time | After Automation | Savings |
|------|-------------|-----------------|---------|
| 1. Review Karbon pending items | 5 min | 0 min (auto-pulled) | 5 min |
| 2. Download payroll | 5 min | ~5 min (Manual: team downloads + uploads pay stubs) | 0 min |
| 3. File documents | 3 min | 0 min (auto-filed) | 3 min |
| 4. Check QBO bank feeds | 5 min | 1 min (review auto-generated health report) | 4 min |
| 5. Fix QBO rules | 5 min | 2 min (AI suggests + human approves rules; n8n virtual rules engine applies them) | 3 min |
| 6. Mass reclassify transactions | 10 min | 3 min (approve proposed reclassification list; n8n applies via QBO API) | 7 min |
| 7. Download financials | 5 min | 0 min (auto-pulled or auto-requested) | 5 min |
| 8. Model estimated taxes | 15 min | 3 min (review auto-populated template) | 12 min |
| 9. Enter W-2 withholding | 5 min | ~1 min (AI reads uploaded pay stub + review) | 4 min |
| 10. Model entity savings | 10 min | 2 min (review auto-calculated comparison) | 8 min |
| 11. Research tax strategies | 15 min | 8 min (review AI research memo — Blue J findings composed by Claude; human validates) | 7 min |
| 12. Build scorecard | 10 min | 2 min (review auto-generated scorecard) | 8 min |
| 13. Write meeting agenda | 5 min | 2 min (review AI-drafted agenda) | 3 min |
| 14. Delegate tasks | 3 min | 0 min (auto-created in Karbon) | 3 min |
| **TOTAL** | **~101 min** | **~29 min** | **~72 min** |

**Notes:**
- "After Automation" times assume the client has API access to accounting (best case)
- Payroll is collected manually (team downloads and uploads pay stubs); the AI then parses the uploaded stub
- Reclassification (step 6) now follows a propose → approve → apply flow: Claude proposes categories, the human approves in a review sheet, and n8n applies the changes via the QBO API
- Categorization rules (step 5) run through n8n's virtual rules engine; Claude suggests new rules from recurring patterns and a human approves before activation
- Tax research (step 11) uses Blue J as the primary research engine; Claude composes a client-specific cited memo, and the professional validates all conclusions
- For non-API accounting clients, add ~10 min for document collection wait time
- Human review time cannot be eliminated — it ensures accuracy

**v2.0 note — net-new intelligence work.** The 14 steps above describe the
historical manual process and are preserved as observed. In addition to
automating these steps, v2.0 also automates intelligence work Karen
previously had no time to do manually at all: reviewing every client email
thread since the last meeting, reviewing the prior meeting's transcript for
promises made, screening the full strategy library against fresh data, and
mining the client's tax returns for planning data. This is net-new value on
top of the time savings shown above, not a reduction of an existing step.

---

## 3. AUTOMATED PROCESS DESIGN

### 3.1 Design Principles

1. **Modular:** Each sub-workflow operates independently and can be
   developed, tested, and maintained separately.

2. **Adaptive:** The system branches based on client profile to handle
   varying tech setups (API vs. manual, QBO vs. Xero vs. nothing).

3. **Fail-safe:** If any sub-workflow fails, the others continue.
   Failures are logged and flagged, never silently ignored.

4. **Human-in-the-loop:** AI generates drafts and calculations;
   humans review and approve before anything reaches the client.

5. **IRS-compliant:** Built entirely with synthetic data. No client
   data flows through development or third-party environments.

### 3.2 System Architecture Overview

```mermaid
flowchart TD
    subgraph TRIGGER["TRIGGER LAYER"]
        CAL[Google Calendar<br/>Event Detection]
        DRIVE[Google Drive<br/>File Watch]
        MANUAL[Manual Trigger<br/>Button in n8n]
    end

    subgraph ROUTING["ROUTING LAYER"]
        PROFILE[Client Profile<br/>Lookup<br/>Google Sheets]
        BRANCH[Branching Logic<br/>API vs Manual<br/>Entity Type<br/>State]
    end

    subgraph COLLECTION["DATA COLLECTION LAYER"]
        KARBON[Karbon<br/>Open items + items<br/>completed since<br/>last meeting]
        QBO[QBO / Xero<br/>Financial Reports +<br/>Close & Hygiene data]
        PAYROLL[Payroll Software<br/>Manual pay stub<br/>download + upload]
        EMAIL[Karbon Client Requests<br/>auto-reminders<br/>Gmail/GHL fallback]
        INTAKE[Google Drive<br/>Document Intake]
        COMMS[Client Communications<br/>Karbon comms API<br/>Gmail search fallback]
        RECAP[Last-Meeting Recap<br/>prior Fathom transcript<br/>feed-forward]
        TAXDOCS[Tax Document<br/>Intelligence<br/>Drive tax folder scan]
        INVENTORY[Client File Inventory<br/>full Drive folder<br/>+ PMT schedule]
        KAREN_IN[Preparer Input Prompt<br/>email Karen at T-48h<br/>non-blocking]
    end

    subgraph PROCESSING["AI PROCESSING LAYER"]
        CLAUDE[Claude AI]
        PARSE[Document Parser<br/>PDF / CSV / Excel]
        CALC[Tax Calculator<br/>Google Sheets]
        SCORE[Scorecard<br/>Generator]
        SCREENER[Tax Strategy<br/>Screener<br/>Strategy Library Sheet]
        HYGIENE[QBO Close &<br/>Hygiene Report<br/>Books Health]
        BRIEF[Meeting Brief<br/>Compiler<br/>9 sections incl. agenda]
    end

    subgraph OUTPUT["OUTPUT LAYER"]
        GDOC[Google Docs<br/>Meeting Brief]
        GSHEET[Google Sheets<br/>Tax Calculator<br/>Scorecard]
        GSLIDE[Google Slides /<br/>Gamma optional<br/>Presentation Deck]
        KARBON_WI[Karbon<br/>Work Item Creation]
        NOTIFY[Email<br/>Notification]
    end

    CAL --> PROFILE
    DRIVE --> INTAKE
    MANUAL --> PROFILE
    PROFILE --> BRANCH
    BRANCH --> KARBON
    BRANCH --> QBO
    BRANCH --> PAYROLL
    BRANCH --> EMAIL
    BRANCH --> COMMS
    BRANCH --> RECAP
    BRANCH --> TAXDOCS
    BRANCH --> INVENTORY
    BRANCH --> KAREN_IN
    PAYROLL --> INTAKE
    INTAKE --> PARSE
    KARBON --> CLAUDE
    QBO --> CALC
    QBO --> HYGIENE
    PARSE --> CALC
    EMAIL --> KARBON_WI
    COMMS --> CLAUDE
    RECAP --> CLAUDE
    TAXDOCS --> CLAUDE
    INVENTORY --> CLAUDE
    KAREN_IN --> CLAUDE
    CALC --> SCORE
    CALC --> CLAUDE
    SCORE --> CLAUDE
    TAXDOCS --> SCREENER
    CALC --> SCREENER
    CLAUDE --> SCREENER
    SCREENER --> BRIEF
    HYGIENE --> BRIEF
    CLAUDE --> BRIEF
    SCORE --> BRIEF
    BRIEF --> GDOC
    BRIEF --> GSLIDE
    SCORE --> GSHEET
    CALC --> GSHEET
    CLAUDE --> KARBON_WI
    GDOC --> NOTIFY
    GSHEET --> NOTIFY
    GSLIDE --> NOTIFY
    KARBON_WI --> NOTIFY
```

**New v2.0 ingestion sources (DATA COLLECTION layer):**

1. **Client Communications Digest.** n8n pulls all client email threads
   since the last meeting via the Karbon communications API (with a Gmail
   search fallback using the profile's `gmail_query_alias`). Claude digests
   them into: commitments made by either side, open questions, life or
   business changes mentioned, and unresolved threads.

2. **Last-Meeting Recap (transcript feed-forward).** The prior meeting's
   Fathom transcript (link stored in the client profile by the post-meeting
   workflow) is fed INTO the next prep. Claude extracts the promises made
   in that meeting and cross-references them against Karbon work items to
   produce a Done / Pending / Blocked report. Previously the transcript was
   only used post-meeting — this closes the loop.

3. **Tax Document Intelligence.** n8n scans the client's Drive tax folder
   (`drive_tax_folder` in the profile) and Claude extracts return data:
   AGI, marginal and effective rates, carryforwards, elections,
   depreciation schedules, safe harbor targets, and estimates paid.

4. **Client File Inventory.** n8n enumerates the FULL client Drive folder
   (not just the current quarter); AI triages what is relevant to this
   meeting and extracts PMT schedule status (payments scheduled vs. made
   vs. upcoming) from the client's PMT file (`pmt_file_link`).

5. **Preparer Input Prompt.** At T-48h, n8n emails Karen: "any updates or
   topics for [CLIENT]?" Her reply is parsed into the brief. This input is
   **non-blocking** — if no reply arrives, the pipeline proceeds at T-24h
   without it.

6. **Completed-work pull.** The Karbon sub-workflow now pulls BOTH open
   items AND items completed since the last meeting, so the brief can tell
   the "what we've done for you" story.

---

## 4. MASTER WORKFLOW ARCHITECTURE

### 4.1 Master Workflow: Quarterly Meeting Prep Pipeline

This is the orchestrating workflow that coordinates all sub-workflows.

```mermaid
flowchart TD
    START([Google Calendar Trigger<br/>48 hours two days<br/>before Quarterly Meeting]) --> EXTRACT[Extract client name<br/>from calendar event]

    EXTRACT --> LOOKUP[Look up client in<br/>Client Profile Matrix<br/>Google Sheets]

    LOOKUP --> VALIDATE{Client profile<br/>found?}

    VALIDATE -->|No| ERROR1[Send alert email<br/>Client profile missing<br/>Prepare manually]

    VALIDATE -->|Yes| PARALLEL

    subgraph PARALLEL["PARALLEL DATA COLLECTION & INGESTION"]
        direction LR
        P1[Sub-Workflow 1<br/>Karbon Pull<br/>open + completed]
        P2[Sub-Workflow 2<br/>Financial Data]
        P3[Sub-Workflow 3<br/>Payroll Data]
        P8[Comms Digest<br/>client emails since<br/>last meeting]
        P9[Last-Meeting Recap<br/>prior transcript<br/>feed-forward]
        P10[Tax Document<br/>Intelligence<br/>Drive tax folder]
        P11[Client File<br/>Inventory<br/>+ PMT status]
        P12[Preparer Input<br/>Prompt to Karen<br/>non-blocking]
    end

    PARALLEL --> WAIT{All data<br/>collected?}

    WAIT -->|Some pending<br/>email requests or<br/>Karen reply| PARTIAL[Continue with<br/>available data at T-24h<br/>Flag gaps]
    WAIT -->|All available| PROCESS

    PARTIAL --> PROCESS

    subgraph PROCESS["AI PROCESSING"]
        direction LR
        P4[Sub-Workflow 4<br/>Tax Estimation]
        P5[Sub-Workflow 5<br/>Scorecard]
        P13[Sub-Workflow 11<br/>Tax Strategy<br/>Screener]
        P14[Sub-Workflow 12<br/>QBO Close &<br/>Hygiene Report]
    end

    PROCESS --> GENERATE

    subgraph GENERATE["DOCUMENT GENERATION"]
        direction LR
        P15[Sub-Workflow 13<br/>Meeting Brief Compiler<br/>9-section Google Doc]
        P16[Sub-Workflow 14<br/>Presentation Deck<br/>Slides or Gamma]
        P7[Sub-Workflow 7<br/>Task Delegation]
    end

    GENERATE --> SAVE[Save all documents<br/>to client Google Drive folder]

    SAVE --> NOTIFY[Send notification<br/>Prep is ready for review]

    NOTIFY --> END([Preparer reviews<br/>and customizes])
```

### 4.2 Trigger Configuration

**Primary Trigger: Google Calendar**
- Polls Google Calendar every 6 hours (or uses webhook)
- Fires 48 hours (two days) before the meeting
- Filters for events containing "Quarterly" in the title or a designated
  calendar label
- Extracts client name from the event title or description
- At T-48h the Preparer Input Prompt email is also sent to Karen; her
  reply is folded into the brief if received, and the pipeline proceeds
  at T-24h without it (non-blocking)

**Secondary Trigger: Manual**
- n8n button that allows a team member to manually trigger the prep
  pipeline for any client at any time
- Useful for ad-hoc meetings or re-running after data updates

**Tertiary Trigger: Google Drive File Watch**
- Monitors client folders for newly uploaded documents
- When a file arrives (from a document request), triggers the intake
  sub-workflow to process it and continue the pipeline

---

## 5. SUB-WORKFLOW DETAILS

### 5.1 Sub-Workflow 1: Karbon Pending & Completed Items

New in v2.0: in addition to open items, this sub-workflow pulls the work
items **completed since the last meeting**, which feed the "Since Last
Meeting" / "what we've done for you" story in the Meeting Brief.

```mermaid
flowchart TD
    IN([Receive<br/>karbon_client_id]) --> AUTH[Authenticate<br/>to Karbon API]
    AUTH --> WORK[Get all work items<br/>status != Complete]
    AUTH --> DONE[Get work items<br/>completed since<br/>last meeting date]
    AUTH --> COMM[Get recent<br/>communications<br/>last 90 days]
    WORK --> FILTER[Filter for<br/>actionable items]
    COMM --> FILTER
    DONE --> STORY[Format completed items<br/>as what we've done<br/>for you summary]
    FILTER --> FORMAT[Format as<br/>structured list]
    FORMAT --> CATEGORIZE[Categorize items<br/>Tax Return / Advisory /<br/> Admin / Client Action]
    CATEGORIZE --> OUT([Return pending +<br/>completed items JSON +<br/>summary text])
    STORY --> OUT

    WORK -->|API Error| FALLBACK[Log error<br/>Flag for manual check]
    FALLBACK --> OUT
```

**API Details:**
- Endpoint: Karbon REST API
- Authentication: OAuth2 or API key
- Rate limits: Respect Karbon's rate limiting (varies by plan)

---

### 5.2 Sub-Workflow 2: Financial Data Collection

```mermaid
flowchart TD
    IN([Receive client profile]) --> CHECK{accounting_access?}

    CHECK -->|API_Full or<br/>API_ReadOnly| API_PATH

    subgraph API_PATH["API PATH"]
        SW{accounting_software?}
        SW -->|QBO| QBO_AUTH[Auth to QBO API]
        SW -->|Xero| XERO_AUTH[Auth to Xero API]

        QBO_AUTH --> QBO_PNL[Pull P&L<br/>Current YTD +<br/>Prior 12mo +<br/>Previous 12mo]
        QBO_AUTH --> QBO_BS[Pull Balance Sheet<br/>Same periods]
        QBO_AUTH --> QBO_BANK[Check bank feed<br/>sync status]

        XERO_AUTH --> XERO_PNL[Pull P&L<br/>Same periods]
        XERO_AUTH --> XERO_BS[Pull Balance Sheet]

        QBO_PNL --> NORMALIZE[Normalize to<br/>standard JSON format]
        QBO_BS --> NORMALIZE
        QBO_BANK --> HEALTH[Generate bank<br/>feed health report]
        XERO_PNL --> NORMALIZE
        XERO_BS --> NORMALIZE

        NORMALIZE --> SAVE_DRIVE[Save CSV/PDF<br/>to Google Drive]
    end

    CHECK -->|Portal_Login| MANUAL_PATH

    subgraph MANUAL_PATH["MANUAL INSTRUCTIONS PATH"]
        INSTRUCT[Generate Scribe-linked<br/>pull instructions for team]
        INSTRUCT --> TASK[Create Karbon work item<br/>Assigned to team member<br/>Due 3 days before meeting]
    end

    CHECK -->|No_Access| REQUEST_PATH

    subgraph REQUEST_PATH["DOCUMENT REQUEST PATH"]
        KCR[Create Karbon client request<br/>via Karbon API<br/>Auto-reminders until upload]
        KCR --> KCR_DETECT[n8n detects request<br/>completion via Karbon API]
        KCR -->|Client request<br/>unavailable| RECIPIENT{bookkeeper_email<br/>exists?}
        RECIPIENT -->|Yes| BK_EMAIL[Fallback: template email<br/>to bookkeeper<br/>Gmail/GoHighLevel]
        RECIPIENT -->|No| CL_EMAIL[Fallback: template email<br/>to client<br/>Gmail/GoHighLevel]
        BK_EMAIL --> REQ_TASK[Create Karbon work item<br/>Awaiting docs from client]
        CL_EMAIL --> REQ_TASK
        KCR_DETECT --> WATCH[Set up Drive<br/>folder watch trigger]
        REQ_TASK --> WATCH
    end

    SAVE_DRIVE --> OUT([Return financial<br/>data JSON])
    HEALTH --> OUT
    TASK --> OUT2([Return manual<br/>task created flag])
    WATCH --> OUT3([Return awaiting<br/>docs flag])
```

**Branch B (no accounting access) — how documents are requested:**

The primary mechanism is a **Karbon Client Request**: n8n creates the
request via the Karbon API, Karbon automatically reminds the client until
they upload the requested documents, and n8n detects completion via the
Karbon API. Templated emails via Gmail or GoHighLevel remain available as
a fallback when a client request cannot be used for a given contact.

**QBO API Details:**
- Base URL: `https://quickbooks.api.intuit.com/v3/company/{companyId}`
- Authentication: OAuth 2.0
- Reports endpoint: `/reports/ProfitAndLoss`, `/reports/BalanceSheet`
- Date parameters: `start_date`, `end_date`
- Sandbox: `https://sandbox-quickbooks.api.intuit.com`

**Xero API Details:**
- Base URL: `https://api.xero.com/api.xro/2.0`
- Authentication: OAuth 2.0
- Reports: `/Reports/ProfitAndLoss`, `/Reports/BalanceSheet`

---

### 5.3 Sub-Workflow 3: Payroll Data Collection

Payroll is collected **manually** — the firm does not connect via API to
client payroll dashboards. When a client has payroll, the team/admin
downloads the pay stubs from the client's payroll software and uploads them
to the client's Google Drive folder. The existing document-intake mechanism
(Claude AI parsing the uploaded pay stub PDF) then extracts the withholding
numbers and feeds the tax calculator. When there is no payroll system, the
step is skipped and the client is treated as distributions-only.

```mermaid
flowchart TD
    IN([Receive client profile]) --> CHECK{has_payroll?}

    CHECK -->|Yes| MANUAL_PATH

    subgraph MANUAL_PATH["MANUAL PAYROLL PATH (no API)"]
        TASK1[Create Karbon work item<br/>Team downloads pay stubs<br/>from payroll software]
        TASK1 --> UPLOAD[Team uploads pay stubs<br/>to client Google Drive folder]
        UPLOAD --> WATCH[Drive folder watch<br/>detects uploaded stubs]
        WATCH --> PARSE[Claude AI parses<br/>uploaded pay stub PDF]
        PARSE --> EXTRACT[Extract per employee:<br/>Gross pay<br/>Federal withholding<br/>State withholding<br/>Health insurance<br/>Retirement contributions]
        EXTRACT --> ANNUALIZE[Annualize projections<br/>YTD / months * 12]
    end

    CHECK -->|None / Skip| NODIST

    subgraph NODIST["NO PAYROLL PATH"]
        FLAG[Flag in prep doc:<br/>No W-2 payroll<br/>Distributions only]
        FLAG --> DIST{API access to<br/>accounting software?}
        DIST -->|Yes| PULL_DIST[Pull distribution<br/>data from Balance Sheet]
        DIST -->|No| MANUAL_DIST[Flag for manual<br/>review of distributions]
    end

    ANNUALIZE --> OUT([Return payroll<br/>data JSON])
    PULL_DIST --> OUT4([Return distribution<br/>data only])
    MANUAL_DIST --> OUT5([Return flag for<br/>manual review])
```

---

### 5.4 Sub-Workflow 4: Tax Estimation Engine

```mermaid
flowchart TD
    IN([Receive financial data<br/>+ payroll data<br/>+ client profile]) --> SELECT{entity_type?}

    SELECT -->|S-Corp| TMPL_S[Load S-Corp<br/>template]
    SELECT -->|C-Corp| TMPL_C[Load C-Corp<br/>template]
    SELECT -->|Multi-Entity| TMPL_M[Load Multi-Entity<br/>template]
    SELECT -->|LLC / Sole Prop| TMPL_L[Load Sole Prop<br/>template]

    TMPL_S --> POPULATE
    TMPL_C --> POPULATE
    TMPL_M --> POPULATE
    TMPL_L --> POPULATE

    POPULATE[Populate template with:<br/>• YTD income<br/>• YTD expenses<br/>• Projected annual totals<br/>• Owner W-2 comp<br/>• Withholdings<br/>• Prior year tax]

    POPULATE --> CALC

    subgraph CALC["CALCULATION ENGINE"]
        FED[Federal tax<br/>calculation]
        STATE[State tax<br/>calculation]
        PTE{has_pte_election?}
        CCORP{has_c_corp?}

        FED --> QTRLY_FED[Quarterly payments<br/>25% / 25% / 25% / 25%]
        STATE --> QTRLY_STATE[Quarterly payments<br/>CA: 30% / 40% / 0% / 30%]

        PTE -->|Yes| PTE_CALC[PTE at 9.3%<br/>of qualifying income]
        PTE -->|No| PTE_SKIP[Skip PTE]

        CCORP -->|Yes| CCORP_CALC[C-Corp tax<br/>21% federal<br/>8.84% CA state]
        CCORP -->|No| CCORP_SKIP[Skip C-Corp]
    end

    CALC --> WITHHOLD[Subtract total<br/>withholdings<br/>and PTE credits]

    WITHHOLD --> NET[Calculate net<br/>estimated payment<br/>per quarter]

    NET --> COMPARE{has_c_corp?}

    COMPARE -->|Yes| SCENARIO

    subgraph SCENARIO["ENTITY COMPARISON"]
        SCEN_A[Scenario A<br/>With C-Corp<br/>Current structure]
        SCEN_B[Scenario B<br/>Without C-Corp<br/>All in S-Corp]
        SCEN_A --> DELTA[Calculate tax<br/>savings delta]
        SCEN_B --> DELTA
    end

    COMPARE -->|No| VALIDATE

    SCENARIO --> VALIDATE

    VALIDATE[Send to Claude AI<br/>for validation<br/>Flag anomalies]

    VALIDATE --> OUT([Return:<br/>• Populated tax template<br/>• Payment schedule<br/>• Entity comparison<br/>• AI validation notes])
```

**State Tax Quarterly Schedules:**

| State | Q1 | Q2 | Q3 | Q4 |
|-------|-----|-----|-----|-----|
| California (individual) | 30% | 40% | 0% | 30% |
| Federal (individual) | 25% | 25% | 25% | 25% |
| California (C-Corp) | 30% | 40% | 0% | 30% |
| Federal (C-Corp) | 25% | 25% | 25% | 25% |

---

### 5.5 Sub-Workflow 5: Client Scorecard

```mermaid
flowchart TD
    IN([Receive financial data<br/>+ payroll data]) --> CALC

    subgraph CALC["SCORECARD CALCULATIONS"]
        REV[Revenue<br/>Last 12mo vs Prior 12mo<br/>$ amount + % change]

        PROFIT[Net Profit Margin<br/>Net Income / Revenue<br/>Both periods]

        TAKE[Owner Take-Home<br/>W-2 salary +<br/>distributions + benefits<br/>Both periods]

        TAX[Tax Efficiency<br/>Effective tax rate<br/>Savings from strategies]
    end

    CALC --> AI[Send to Claude AI<br/>Generate 2-3 sentence<br/>narrative explaining trends]

    AI --> FORMAT[Format for<br/>presentation]

    FORMAT --> GSHEET[Write to Google Sheets<br/>scorecard template]
    FORMAT --> GSLIDE[Write to Google Slides<br/>scorecard slide]

    GSHEET --> OUT([Return scorecard<br/>data + narrative])
    GSLIDE --> OUT
```

**Scorecard Output Format:**

```
┌─────────────────────────────────────────────────────────┐
│                  CLIENT SCORECARD                        │
│                  Q1 2026 Review                          │
├──────────────┬──────────────┬──────────────┬────────────┤
│   REVENUE    │  TAKE-HOME   │    PROFIT    │    TAX     │
│              │              │              │  SAVINGS   │
│  $XXX,XXX   │   $XX,XXX    │    XX.X%     │  $X,XXX    │
│   ▲ XX%     │    ▲ XX%     │    ▼ X.X%    │            │
│ vs prior yr  │ vs prior yr  │ vs prior yr  │ this year  │
└──────────────┴──────────────┴──────────────┴────────────┘

Narrative: Revenue grew 19% driven by the [company] acquisition.
Profit margin compressed slightly due to acquisition-related
interest expense. Take-home increased via distributions.
Tax savings of $9,256 from the new C-Corp entity structure.
```

---

### 5.6 Sub-Workflow 6: Meeting Agenda Generation

**v2.0 note:** the agenda generator is now a **component of the Meeting
Brief Compiler (Sub-Workflow 13)** — its output becomes the "Key Talking
Points" and related sections of the 9-section Meeting Brief rather than a
standalone document. The flow below is unchanged internally.

```mermaid
flowchart TD
    IN([Receive:<br/>• Pending items<br/>• Tax estimation<br/>• Scorecard<br/>• Client profile<br/>• Blue J research memo<br/>• Pre-meeting questionnaire<br/>responses]) --> COMPILE[Compile all inputs<br/>into structured prompt]

    COMPILE --> CLAUDE[Send to Claude AI<br/>with agenda template<br/>instructions]

    CLAUDE --> STRUCTURE

    subgraph STRUCTURE["AGENDA STRUCTURE"]
        SEC1["1. QUICK WIN<br/>Tax savings highlight<br/>Strategy success"]
        SEC2["2. SCORECARD REVIEW<br/>4 metrics with narrative<br/>Tax story focus"]
        SEC3["3. ESTIMATED TAX PAYMENTS<br/>Exact amounts + due dates<br/>Federal + State + PTE"]
        SEC4["4. NEXT 90 DAYS<br/>2-3 action items<br/>Strategies to explore"]
        SEC5["5. OPEN ITEMS<br/>Pending from Karbon<br/>Client questions"]
    end

    STRUCTURE --> FORMAT_DOC[Format as<br/>Google Doc]
    STRUCTURE --> FORMAT_SLIDE[Format as<br/>Google Slides]

    FORMAT_DOC --> SAVE[Save to client<br/>Google Drive folder]
    FORMAT_SLIDE --> SAVE

    SAVE --> OUT([Return document<br/>links])
```

---

### 5.7 Sub-Workflow 7: Task Delegation

```mermaid
flowchart TD
    IN([Receive flags from<br/>all sub-workflows]) --> CATEGORIZE

    subgraph CATEGORIZE["CATEGORIZE FLAGS"]
        ADMIN[Admin Tasks<br/>Approve reclassification<br/>proposals / new rules<br/>Document filing]
        REVIEW[Review Tasks<br/>Verify numbers<br/>Check reimbursements<br/>Confirm payments]
        CLIENT_A[Client Actions<br/>Upload documents<br/>Sign forms<br/>Make payments]
    end

    ADMIN --> KARBON_ADMIN[Create Karbon work item<br/>Assign to admin team<br/>Due 2 days before meeting]
    REVIEW --> KARBON_REVIEW[Create Karbon work item<br/>Assign to preparer<br/>Due 1 day before meeting]
    CLIENT_A --> GHL[Draft email to client<br/>via GoHighLevel or Gmail<br/>List their action items]

    KARBON_ADMIN --> KARBON_UPDATE[Update Karbon<br/>work item status]
    KARBON_REVIEW --> KARBON_UPDATE
    GHL --> KARBON_UPDATE

    KARBON_UPDATE --> OUT([Return task IDs<br/>and notification status])
```

---

### 5.8 Sub-Workflow 8: Post-Meeting Actions (Fathom Integration)

```mermaid
flowchart TD
    MEETING([Client Meeting<br/>Completed]) --> FATHOM[Fathom generates<br/>transcript + summary]

    FATHOM --> DETECT[n8n detects new<br/>Fathom transcript<br/>via API poll or webhook]

    DETECT --> CLAUDE[Send transcript<br/>to Claude AI]

    CLAUDE --> EXTRACT[Extract action items<br/>• Who is responsible<br/>• What needs to be done<br/>• Suggested deadline<br/>• Priority level]

    EXTRACT --> SPLIT{Who owns<br/>the action?}

    SPLIT -->|Firm team| KARBON_TASK[Create Karbon work item<br/>with context]
    SPLIT -->|Client| EMAIL_DRAFT[Draft follow-up email<br/>listing client actions]

    KARBON_TASK --> KARBON[Update Karbon<br/>with meeting notes<br/>and next steps]
    EMAIL_DRAFT --> KARBON

    KARBON --> PROFILE_UPDATE[Update Client Profile<br/>last_meeting_date<br/>last_meeting_transcript_link<br/>next quarter goals]

    PROFILE_UPDATE --> OUT([Post-meeting<br/>processing complete<br/>transcript feeds next<br/>quarter's prep])
```

---

### 5.9 Sub-Workflow 9: Transaction Reclassification Engine

Mass reclassification is no longer a manual step. It follows a
**propose → approve → apply** pattern: n8n pulls uncategorized or
suspect transactions via the QBO API, Claude proposes a target category
and class for each transaction, the proposals land in a
"Reclassification Review" Google Sheet with Approve checkboxes, and once
approved, n8n applies the changes via QBO API batch/sparse updates. Every
change is written to a full audit log. If API-based updates are ever
insufficient, the fallback is SaasAnt Transactions (~$20/mo, optional) or
Antigravity RPA.

```mermaid
flowchart TD
    IN([Trigger: prep pipeline<br/>or scheduled run]) --> PULL[Pull transactions<br/>via QBO API<br/>uncategorized + suspect]

    PULL --> PROPOSE[Claude proposes target<br/>category + class<br/>per transaction<br/>with confidence + rationale]

    PROPOSE --> SHEET[Write proposals to<br/>Reclassification Review<br/>Google Sheet<br/>with Approve checkboxes]

    SHEET --> NOTIFY_REV[Notify reviewer<br/>proposals ready]

    NOTIFY_REV --> APPROVE{Human approves<br/>each proposal?}

    APPROVE -->|Approved rows| APPLY[n8n applies changes<br/>via QBO API<br/>batch / sparse updates]
    APPROVE -->|Rejected rows| SKIP[Leave unchanged<br/>log rejection reason]

    APPLY --> AUDIT[Append to full<br/>audit log sheet<br/>who / what / when / before-after]
    SKIP --> AUDIT

    APPLY -->|API update<br/>not possible| FALLBACK[Fallback:<br/>SaasAnt Transactions<br/>~$20/mo optional<br/>or Antigravity RPA]
    FALLBACK --> AUDIT

    AUDIT --> OUT([Return applied /<br/>rejected counts +<br/>audit log link])
```

---

### 5.10 Sub-Workflow 10: Virtual Categorization Rules Engine

QBO's bank-feed categorization rules are **not editable via the QBO
API**, so instead of editing QBO's rules, n8n runs its own "virtual
rules engine" on a weekly schedule. Rules live in a Google Sheet
(description / amount / account match → category / class). n8n applies
matching rules directly to transactions via the QBO API, and Claude
suggests new rules from recurring patterns — a human approves every
suggested rule before it becomes active.

```mermaid
flowchart TD
    SCHED([Weekly schedule<br/>trigger]) --> RULES[Load active rules from<br/>Rules Google Sheet<br/>description / amount /<br/>account match →<br/>category / class]

    RULES --> TXN[Pull new transactions<br/>via QBO API]

    TXN --> MATCH{Transaction matches<br/>an active rule?}

    MATCH -->|Yes| APPLY_RULE[Apply category + class<br/>via QBO API]
    MATCH -->|No| PATTERN[Collect unmatched<br/>transactions]

    APPLY_RULE --> LOG[Write to<br/>audit log sheet]

    PATTERN --> SUGGEST[Claude analyzes<br/>recurring patterns<br/>Suggests new rules]

    SUGGEST --> PENDING[Write suggestions to<br/>Rules Sheet as<br/>Pending Approval]

    PENDING --> HUMAN{Human approves<br/>rule?}

    HUMAN -->|Yes| ACTIVATE[Mark rule Active<br/>applies from next run]
    HUMAN -->|No| REJECT[Mark rule Rejected<br/>keep for reference]

    ACTIVATE --> LOG
    REJECT --> LOG

    LOG --> OUT([Return rules applied +<br/>new suggestions count])
```

---

### 5.11 Sub-Workflow 11: Tax Strategy Screener

The highest-value addition in v2.0. A **Strategy Library** Google Sheet is
seeded with **~35 tax strategies** across ten categories (entity &
compensation, retirement, real estate, family, health & fringe, credits,
charitable, investment & exit, timing, state) — see the Developer
Requirements Specification, Sub-Workflow 17, for the full seed list. Each
row carries trigger conditions, a savings heuristic, **authority
citations, a risk rating (Conservative / Moderate / Aggressive), and
economic substance notes**. A representative sample:

| # | Strategy | Example Trigger Condition |
|---|----------|---------------------------|
| 1 | S-Corp reasonable compensation optimization | S-Corp with owner W-2 far from comp benchmark |
| 2 | Pass-through entity (PTE) election | Pass-through in a PTE state, no election on file |
| 3 | Augusta rule (Section 280A(g)) | Owner with a personal residence + business meetings |
| 4 | Cost segregation + bonus depreciation | Building/improvements on the balance sheet |
| 5 | Real estate professional status | Significant rental losses + hours threshold plausible |
| 6 | Solo 401(k) / defined benefit plan | High profit, low current retirement deferrals |
| 7 | Hiring children | Owner with minor children, sole prop or family entity |
| 8 | Accountable plan | S-Corp owner paying business costs personally |
| 9 | HRA / ICHRA | Owner-employees with unreimbursed health costs |
| 10 | HSA maximization | HDHP coverage, HSA not maxed |
| 11 | QSBS (Section 1202) | C-Corp stock, potential exit horizon |
| 12 | R&D credit | Software/product development spend |
| 13 | Entity restructuring | Profit level crossing entity break-even thresholds |
| 14 | Income timing / deferral | Large projected income swing vs. prior year |
| 15 | Charitable bunching / DAF | Regular giving near the standard deduction line |

Each quarter, n8n + Claude screen **every** strategy in the library
against fresh client data (QBO financials + extracted tax position +
client profile + questionnaire responses). Strategies already implemented
or previously rejected for the client are filtered out; remaining matches
are ranked by estimated savings, and the **top 2-3** get Blue J-validated
research memos (Claude composes; the professional validates).

**The library is fully extensible — custom and creative strategies
welcome.** Four intake paths, all landing as *Draft* rows that require
Firm approval before they ever screen against a client:

1. **Manual add** — anyone at the Firm adds a row anytime
2. **AI strategy discovery** — during each screening run, Claude also
   answers "are there opportunities NOT in the library for this fact
   pattern?" and writes suggestions to a Proposed Strategies tab
3. **Transcript mining** — strategies discussed on client calls that
   aren't in the library are auto-proposed as Draft rows by the
   post-meeting workflow
4. **Quarterly law-change sweep** — Claude + Blue J review recent
   federal/state tax law changes and propose new or updated rows

Guardrails: Draft rows never screen against clients; every row needs
authority citations; **Aggressive-rated strategies always require a
Blue J-validated memo AND explicit preparer sign-off** before appearing
in any brief; strategies resembling IRS listed/reportable transactions
are excluded by policy.

```mermaid
flowchart TD
    IN([Trigger: prep pipeline<br/>fresh client data ready]) --> LIB[Load Strategy Library<br/>Google Sheet<br/>~35 strategies, extensible<br/>trigger conditions + risk rating +<br/>savings heuristics]

    LIB --> DATA[Assemble client data:<br/>QBO financials +<br/>tax position from<br/>Tax Document Intelligence +<br/>client profile +<br/>questionnaire responses]

    DATA --> SCREEN[Claude screens EVERY<br/>strategy against<br/>client data]

    SCREEN --> HISTORY{Already implemented<br/>or previously rejected<br/>for this client?}

    HISTORY -->|Yes| DROP[Filter out<br/>log reason]
    HISTORY -->|No| ESTIMATE[Estimate savings<br/>using library heuristics<br/>+ client numbers]

    ESTIMATE --> RANK[Rank strategies by<br/>estimated savings]

    RANK --> TOP[Select top 2-3<br/>opportunities]

    TOP --> MEMO[Blue J-validated<br/>research memo per pick<br/>Claude composes<br/>professional validates]

    MEMO --> OUT([Return ranked list +<br/>memos for the<br/>Strategy Opportunities<br/>brief section])
    DROP --> OUT
```

---

### 5.12 Sub-Workflow 12: QBO Close & Hygiene Report

Produces the **"Books Health"** section of the Meeting Brief, with a
month-end close checklist.

```mermaid
flowchart TD
    IN([Trigger: prep pipeline<br/>QBO API access]) --> PULL

    subgraph PULL["HYGIENE DATA PULL (QBO API)"]
        UNCAT[Uncategorized<br/>transaction list]
        RECON[Last reconciliation<br/>dates per account]
        FEED[Bank feed lag<br/>days since last sync]
        AGING[A/R + A/P<br/>aging reports]
    end

    UNCAT --> RECLASS[Feed existing<br/>Reclassification Engine<br/>Sub-Workflow 9]
    UNCAT --> ANALYZE
    RECON --> ANALYZE
    FEED --> ANALYZE
    AGING --> ANALYZE

    ANALYZE[Claude analyzes<br/>for anomalies:<br/>stale reconciliations<br/>aging spikes<br/>unusual balances]

    ANALYZE --> REPORT[Compose Books Health<br/>section + month-end<br/>close checklist]

    REPORT --> OUT([Return Books Health<br/>report for the brief])
```

---

### 5.13 Sub-Workflow 13: Meeting Brief Compiler

Compiles everything into **one Google Doc** — the Meeting Brief — with 9
sections. The former standalone agenda generator (Sub-Workflow 6) is now a
component of this compiler.

**The 9 brief sections:**

1. **Executive Summary**
2. **Since Last Meeting** (comms digest + completed Karbon work)
3. **Follow-Up Items** (transcript feed-forward: Done / Pending / Blocked)
4. **Financial Review** (scorecard + CFO talking points framed in the tax
   story)
5. **Books Health** (QBO Close & Hygiene Report)
6. **Tax Position** (incl. PMT schedule status)
7. **Strategy Opportunities** (ranked screener output + memos)
8. **Key Talking Points**
9. **Questions for Client**

```mermaid
flowchart TD
    subgraph INPUTS["ALL INPUTS CONVERGE"]
        I1[Karbon open +<br/>completed items]
        I2[Client Communications<br/>Digest]
        I3[Last-Meeting Recap<br/>Done/Pending/Blocked]
        I4[Scorecard +<br/>financial data]
        I5[Books Health report]
        I6[Tax Estimation +<br/>Tax Document Intelligence<br/>+ PMT schedule status]
        I7[Strategy Screener<br/>ranked opportunities]
        I8[Preparer input<br/>Karen's reply if any]
        I9[Questionnaire<br/>responses]
    end

    I1 --> COMPILE
    I2 --> COMPILE
    I3 --> COMPILE
    I4 --> COMPILE
    I5 --> COMPILE
    I6 --> COMPILE
    I7 --> COMPILE
    I8 --> COMPILE
    I9 --> COMPILE

    COMPILE[Claude compiles the<br/>9-section Meeting Brief<br/>agenda generator runs<br/>as a component]

    COMPILE --> GDOC[Write single<br/>Google Doc<br/>Meeting Brief]

    GDOC --> DECK[Feed Presentation<br/>Deck Generator<br/>Sub-Workflow 14]
    GDOC --> SAVE[Save to client<br/>Drive folder]

    SAVE --> OUT([Return brief link<br/>for approval gate])
```

---

### 5.14 Sub-Workflow 14: Presentation Deck Generator

Two paths, both released only through the **existing approval gate**
(Section 8.2): the default auto-fills a Google Slides template from the
brief; the optional path uses the **Gamma API** (the firm has Gamma) for
polished AI-generated decks.

```mermaid
flowchart TD
    IN([Receive approved-draft<br/>Meeting Brief content]) --> MODE{Deck mode<br/>per client profile<br/>or preparer choice?}

    MODE -->|Default| SLIDES[Auto-fill Google Slides<br/>template from brief:<br/>scorecard visual<br/>tax savings<br/>strategy picks<br/>next steps]

    MODE -->|Optional| GAMMA[Gamma API<br/>AI-generated deck<br/>from brief content]

    SLIDES --> REVIEW[Attach deck to<br/>prep package]
    GAMMA --> REVIEW

    REVIEW --> GATE{Existing approval gate<br/>Approve /<br/>Request Changes}

    GATE -->|Approve| RELEASE[Deck released with<br/>client-facing package]
    GATE -->|Request Changes| REVISE[Route back<br/>with comments]
    REVISE --> IN

    RELEASE --> OUT([Return deck link])
```

---

## 6. CLIENT PROFILE ADAPTIVE SYSTEM

### 6.1 How Profiles Drive Workflow Behavior

```mermaid
flowchart TD
    PROFILE[(Client Profile<br/>Google Sheets)] --> READ[n8n reads<br/>profile row]

    READ --> B1{accounting_access}
    READ --> B2{has_payroll}
    READ --> B3{entity_type}
    READ --> B4{state_primary}

    B1 -->|API_Full| QBO_API[Auto-pull reports<br/>via API]
    B1 -->|Portal_Login| QBO_MANUAL[Generate pull<br/>instructions]
    B1 -->|No_Access| QBO_EMAIL[Create Karbon client request<br/>auto-reminders<br/>email fallback]

    B2 -->|Yes| PAY_MANUAL[Manual: team downloads<br/>+ uploads pay stubs<br/>AI parses uploaded stub]
    B2 -->|None| PAY_SKIP[Skip payroll<br/>distributions only]

    B3 -->|S-Corp| TAX_S[S-Corp tax template]
    B3 -->|C-Corp| TAX_C[C-Corp tax template]
    B3 -->|Multi-Entity| TAX_M[Multi-entity template<br/>+ comparison model]
    B3 -->|LLC / Sole Prop| TAX_L[Sole Prop template]

    B4 -->|CA| STATE_CA[CA quarterly schedule<br/>30/40/0/30<br/>+ PTE if elected]
    B4 -->|NY| STATE_NY[NY quarterly schedule<br/>+ PTET if elected]
    B4 -->|TX| STATE_TX[No state income tax<br/>Federal only]
    B4 -->|Other| STATE_O[Load state-specific<br/>schedule]
```

### 6.2 Client Profile Matrix Example

| Field | Client A | Client B | Client C |
|-------|----------|----------|----------|
| entity_type | S-Corp + C-Corp | S-Corp | Sole Prop |
| accounting_software | QBO | Xero | None |
| accounting_access | API_Full | API_Full | No_Access |
| payroll_software | Rippling | None | None |
| has_payroll | Yes (manual) | No | No |
| state_primary | CA | NY | TX |
| has_c_corp | Yes | No | No |
| has_pte_election | Yes | Yes | No |
| meeting_cadence | Quarterly | Quarterly | Semi_Annual |
| gmail_query_alias | from:candace@… | from:clientb@… | from:clientc@… |
| drive_tax_folder | /ClientA/Tax | /ClientB/Tax | /ClientC/Tax |
| pmt_file_link | (Drive link) | (Drive link) | (Drive link) |
| last_meeting_transcript_link | (Fathom link) | (Fathom link) | (empty — first meeting) |

**New v2.0 profile fields:** `gmail_query_alias` drives the Gmail fallback
search for the Communications Digest; `drive_tax_folder` points Tax
Document Intelligence at the right folder; `pmt_file_link` locates the PMT
schedule for the File Inventory; `last_meeting_transcript_link` is written
by the post-meeting workflow and read by the Last-Meeting Recap
feed-forward.

**Workflow behavior per client:**

- **Client A**: Full automation — API pull from QBO, payroll collected
  manually (team downloads + uploads pay stubs, AI parses the uploaded
  stub), multi-entity tax template with comparison, CA PTE calculation,
  auto-generated scorecard and agenda.

- **Client B**: Partial automation — API pull from Xero (normalized
  to QBO format), no payroll (distributions only), single entity
  template, NY PTET calculation.

- **Client C**: Request-driven — Karbon client request created for the
  client (auto-reminders until upload; templated email as fallback),
  Drive watch trigger awaits uploads, Claude AI parses uploaded PDFs,
  simple sole prop tax template, federal only.

---

## 7. TAX ESTIMATION ENGINE

### 7.1 Calculation Flow

```mermaid
flowchart TD
    subgraph INPUTS["INPUT DATA"]
        INC[YTD Income<br/>from P&L]
        EXP[YTD Expenses<br/>from P&L]
        W2[Owner W-2<br/>from Payroll]
        WITH[Tax Withholdings<br/>from Payroll]
        PRIOR[Prior Year Tax<br/>from Client Profile]
    end

    INC --> PROJ[Project Annual<br/>Income = YTD / months * 12]
    EXP --> PROJ2[Project Annual<br/>Expenses = YTD / months * 12]

    PROJ --> NET[Net Profit =<br/>Projected Income -<br/>Projected Expenses]
    PROJ2 --> NET

    NET --> PASSTHRU[Pass-through Income<br/>to owner = Net Profit<br/>times ownership %]

    W2 --> TOTAL_INC[Total Taxable Income =<br/>Pass-through +<br/>W-2 Wages +<br/>Other Income]

    PASSTHRU --> TOTAL_INC

    TOTAL_INC --> FED_TAX[Federal Tax<br/>using marginal brackets]
    TOTAL_INC --> STATE_TAX[State Tax<br/>using state brackets]

    FED_TAX --> TOTAL_TAX[Total Tax Liability]
    STATE_TAX --> TOTAL_TAX

    WITH --> CREDITS[Total Credits =<br/>Withholdings +<br/>PTE Credits +<br/>Other Credits]

    TOTAL_TAX --> BALANCE[Balance Due =<br/>Total Tax -<br/>Total Credits]
    CREDITS --> BALANCE

    BALANCE --> QUARTERLY[Quarterly Payment =<br/>Balance Due<br/>divided per state schedule]

    subgraph CCORP_CALC["C-CORP CALCULATION (if applicable)"]
        CCORP_INC[C-Corp<br/>Taxable Income]
        CCORP_FED[Federal: 21%<br/>flat rate]
        CCORP_STATE[CA State: 8.84%<br/>flat rate]
        CCORP_INC --> CCORP_FED
        CCORP_INC --> CCORP_STATE
        CCORP_FED --> CCORP_QTRLY[C-Corp quarterly<br/>payments]
        CCORP_STATE --> CCORP_QTRLY
    end

    QUARTERLY --> SUMMARY[Payment Summary<br/>by entity by quarter]
    CCORP_QTRLY --> SUMMARY
```

### 7.2 Entity Comparison Model

For multi-entity clients (S-Corp + C-Corp), the system calculates
both scenarios:

```
SCENARIO A: Current Structure (with C-Corp)
├── S-Corp pass-through income: $XXX,XXX
├── C-Corp taxable income: $XXX,XXX
├── Individual federal tax: $XX,XXX
├── Individual state tax: $XX,XXX
├── C-Corp federal tax: $XX,XXX
├── C-Corp state tax: $XX,XXX
└── TOTAL TAX: $XXX,XXX

SCENARIO B: Without C-Corp (all in S-Corp)
├── S-Corp pass-through income: $XXX,XXX (includes former C-Corp income)
├── Individual federal tax: $XX,XXX
├── Individual state tax: $XX,XXX
└── TOTAL TAX: $XXX,XXX

TAX SAVINGS = Scenario B Total - Scenario A Total = $X,XXX
```

---

## 8. SCORECARD AND MEETING OUTPUT

### 8.1 Meeting Prep Package

The complete output for each client meeting now centers on the
**Meeting Brief** (one 9-section Google Doc) plus the presentation deck:

```
Client Meeting Prep Package
├── 📘 MEETING BRIEF (Google Docs — the centerpiece)
│   ├── 1. Executive Summary
│   ├── 2. Since Last Meeting (comms digest + completed Karbon work)
│   ├── 3. Follow-Up Items (transcript feed-forward: Done/Pending/Blocked)
│   ├── 4. Financial Review (scorecard + CFO talking points, tax story)
│   ├── 5. Books Health (QBO close & hygiene report + close checklist)
│   ├── 6. Tax Position (incl. PMT schedule status)
│   ├── 7. Strategy Opportunities (top 2-3 ranked, with memos)
│   ├── 8. Key Talking Points
│   └── 9. Questions for Client
│
├── 🎯 Presentation Deck (Google Slides default / Gamma optional)
│   ├── Auto-filled from the Meeting Brief
│   ├── Scorecard + tax savings visuals
│   └── Strategy picks + next steps summary
│
├── 📊 Client Scorecard (Google Sheets — feeds brief section 4)
│   ├── Revenue comparison (12mo vs prior 12mo)
│   ├── Profit margin comparison
│   ├── Owner take-home comparison
│   └── Tax savings / efficiency metrics
│
├── 🧮 Tax Estimation Calculator (Google Sheets — feeds brief section 6)
│   ├── Projected annual income
│   ├── Estimated tax liability
│   ├── Quarterly payment schedule
│   ├── Entity comparison (if multi-entity)
│   └── AI validation notes
│
├── ✅ Task List (Karbon work items)
│   ├── Pre-meeting prep tasks
│   ├── Items needing team action
│   └── Client follow-up items
│
└── 📌 Status Flags
    ├── Data gaps (what's missing, incl. no Karen reply)
    ├── Anomalies detected by AI
    └── Items requiring human judgment
```

### 8.2 Approval Gates & Client Touchpoints

Four conveniences wrap the prep pipeline in lightweight controls and
client-facing touchpoints:

1. **One-click approval gates.** The "prep is ready" email to the
   preparer includes **Approve** and **Request Changes** links, backed by
   an n8n human-in-the-loop webhook. Nothing client-facing (meeting brief,
   presentation deck, scorecard, payment schedule) is released until the preparer clicks
   Approve; Request Changes routes the package back with a comment field.

2. **Pre-meeting client questionnaire.** A short form (3-5 questions —
   e.g., major purchases planned, life/business changes, topics to
   discuss) is sent with the meeting reminder. Responses feed the agenda
   generator (Sub-Workflow 6 input), so the agenda reflects what the
   client actually wants to cover.

3. **Payment reminder workflow.** After the preparer approves the prep
   package, n8n schedules reminder emails to the client and the internal
   payments coordinator ahead of each federal and CA estimated-payment
   due date, including the exact amounts and direct links to EFTPS and
   CA FTB Web Pay.

4. **Monitoring.** Every execution appends a row to a run-log Google
   Sheet (client, trigger, steps completed, flags, duration, outcome). A
   free **Looker Studio** dashboard on top of that sheet shows prep
   status per client, missing documents, open flags, and upcoming
   meetings. Failures trigger an alert email immediately, and a weekly
   digest summarizes all runs.

```mermaid
flowchart LR
    PREP[Prep package<br/>generated] --> GATE{One-click gate:<br/>Approve /<br/>Request Changes}
    GATE -->|Approve| RELEASE[Release client-facing<br/>outputs]
    GATE -->|Request Changes| REVISE[Route back to<br/>pipeline with comments]
    REVISE --> PREP
    RELEASE --> PAYREM[Schedule payment<br/>reminders<br/>EFTPS + CA FTB Web Pay]
    QUEST[Pre-meeting<br/>questionnaire<br/>3-5 questions] --> AGENDA_IN[Agenda generator<br/>input]
    PREP --> RUNLOG[Run-log<br/>Google Sheet]
    RUNLOG --> LOOKER[Looker Studio<br/>dashboard]
    RUNLOG --> ALERTS[Failure alerts +<br/>weekly digest]
```

---

## 9. POST-MEETING AUTOMATION

### 9.1 Post-Meeting Flow

```mermaid
flowchart LR
    MEET[Client Meeting<br/>via Zoom/Teams] --> FATHOM[Fathom records<br/>and transcribes]
    FATHOM --> N8N[n8n detects<br/>new transcript]
    N8N --> CLAUDE[Claude extracts<br/>action items]
    CLAUDE --> TASKS[Karbon work items<br/>created]
    CLAUDE --> EMAIL[Client follow-up<br/>email drafted]
    TASKS --> KARBON[Karbon updated<br/>with notes]
    EMAIL --> KARBON
    KARBON --> PROFILE[Client Profile updated:<br/>next quarter goals +<br/>last_meeting_transcript_link]
    PROFILE -.->|Feed-forward: transcript<br/>read by next quarter's<br/>Last-Meeting Recap| NEXT[Next quarter's<br/>prep pipeline]
```

**Closing the feed-forward loop (v2.0):** the post-meeting workflow now
stores the Fathom transcript link in the client profile
(`last_meeting_transcript_link`). The next quarter's prep pipeline reads
it in the Last-Meeting Recap ingestion step, extracting promises made and
cross-referencing Karbon work items into a Done / Pending / Blocked
report.

---

## 10. ERROR HANDLING AND EDGE CASES

### 10.1 Error Handling Strategy

```mermaid
flowchart TD
    ERROR{Error Type} --> API_ERR[API Error<br/>timeout / auth failure]
    ERROR --> DATA_ERR[Data Error<br/>missing / malformed]
    ERROR --> AI_ERR[AI Error<br/>unexpected response]
    ERROR --> QUOTA[Rate Limit<br/>API throttled]

    API_ERR --> RETRY[Retry with<br/>exponential backoff<br/>3 attempts]
    RETRY --> RETRY_OK{Success?}
    RETRY_OK -->|Yes| CONTINUE[Continue workflow]
    RETRY_OK -->|No| FLAG_API[Flag: API unavailable<br/>Skip this sub-workflow<br/>Add to manual checklist]

    DATA_ERR --> VALIDATE[Attempt data<br/>normalization]
    VALIDATE --> VALID{Usable?}
    VALID -->|Yes| CONTINUE
    VALID -->|No| FLAG_DATA[Flag: Data quality issue<br/>Include what was expected<br/>vs what was received]

    AI_ERR --> REPROMPT[Retry with<br/>simplified prompt]
    REPROMPT --> AI_OK{Success?}
    AI_OK -->|Yes| CONTINUE
    AI_OK -->|No| FLAG_AI[Flag: AI processing failed<br/>Include raw data for<br/>manual processing]

    QUOTA --> WAIT[Wait and retry<br/>after cooldown]
    WAIT --> CONTINUE

    FLAG_API --> NOTIFY[Add to prep doc<br/>Items Needing Manual Attention]
    FLAG_DATA --> NOTIFY
    FLAG_AI --> NOTIFY
```

### 10.2 Common Edge Cases

| Edge Case | How the System Handles It |
|-----------|--------------------------|
| Client has no financial data yet (new client) | Skip scorecard, use simplified agenda, flag for discovery meeting |
| Payroll system changed mid-year | Use most recent payroll source, flag discrepancy for review |
| Multi-state client with different entity in each state | Load state-specific template for each entity, calculate separately |
| Client switched from S-Corp to C-Corp mid-year | Flag for manual tax calculation (complex transition rules) |
| QBO bank feed is months behind | Flag prominently: "Bank feeds last synced [date]. Financial data may be stale." |
| Prior year tax data not available | Use safe harbor estimate (110% of known prior year liability) or flag |
| Google Drive folder doesn't exist | Auto-create folder structure following naming convention |
| Calendar event has no client name | Send alert to preparer: "Calendar event found but client not identified" |

---

## 11. AUTOMATION CLASSIFICATION

### 11.1 Complete Summary

```mermaid
pie title Automation Coverage (14 Process Steps)
    "Fully Automated (4)" : 4
    "AI-Assisted — Human Review (9)" : 9
    "Manual (1)" : 1
```

### 11.2 Detailed Classification

#### Fully Automated (4 steps — no human touch needed)

| Step | What | How |
|------|------|-----|
| 1. Karbon pending items | Pull open work items | n8n + Karbon API |
| 3. File organization | Create folders, save documents | n8n + Google Drive API |
| 7. Financial report download | Pull P&L and Balance Sheet | n8n + QBO/Xero API |
| 14. Task delegation | Create Karbon work items for team | n8n + Karbon API |

#### AI-Assisted — Human Review Required (9 steps)

| Step | What | AI Does | Human Does |
|------|------|---------|------------|
| 4. Bank feed review | Check bank sync and categorization | Detects anomalies, flags issues | Investigates root cause |
| 5. Categorization rules | Maintain n8n virtual rules engine (QBO bank-feed rules aren't editable via API) | Suggests new rules from recurring patterns; n8n applies active rules via QBO API weekly | Approves each suggested rule before activation |
| 6. Mass reclassify transactions | Propose → approve → apply reclassification | Proposes category/class per transaction; n8n applies approved changes via QBO API batch updates with audit log | Approves/rejects proposals in the Reclassification Review sheet |
| 8. Tax estimation | Calculate quarterly estimated payments | Populates template, validates | Reviews projections, applies judgment |
| 9. W-2 withholding entry | Read withholding from uploaded pay stub | Parses uploaded stub, populates tax template | Reviews extracted figures |
| 10. Entity comparison | Model tax with vs. without C-Corp | Calculates both scenarios | Validates assumptions |
| 11. Tax strategy research | Research strategies via Blue J + memo drafting | Blue J surfaces cited research; Claude composes a client-specific cited memo; NotebookLM cross-checks | Validates all conclusions and applies professional judgment |
| 12. Client scorecard | Build 4-metric performance report | Calculates metrics, writes narrative | Reviews narrative accuracy |
| 13. Meeting agenda | Draft structured meeting agenda | Generates from all collected data | Customizes, adds personal insights |

#### Manual — By Firm Choice (1 step)

| Step | What | Why It Stays Manual |
|------|------|----------------------|
| 2. Payroll download | Download pay stubs from payroll software, upload to Drive | By firm choice — no connections to client payroll dashboards; pay stubs are downloaded and uploaded manually. (Optional future avenue: a dedicated intake mailbox where clients email stubs in — still no payroll logins. See Future Enhancements.) |

---

## 12. IMPLEMENTATION ROADMAP

### 12.1 Phased Rollout

```mermaid
gantt
    title Implementation Roadmap (3 Weeks)
    dateFormat YYYY-MM-DD
    axisFormat %b %d

    section Week 1 - Foundation & Data Collection
    Client Profile + folders + email templates :p1a, 2026-07-01, 2d
    QBO + Xero auto-pull workflows              :p1b, 2026-07-01, 4d
    Karbon pending items pull                   :p1c, 2026-07-02, 2d
    Document request emails + Drive intake      :p1d, 2026-07-03, 3d
    Manual payroll upload + AI parse            :p1e, 2026-07-03, 3d
    Karbon client requests + auto-reminders     :p1f, 2026-07-03, 3d
    Comms digest (Karbon comms + Gmail fallback) :p1g, 2026-07-04, 3d
    Transcript feed-forward (last-meeting recap) :p1h, 2026-07-04, 3d
    Tax document intelligence (Drive tax folder) :p1i, 2026-07-05, 3d
    Client file inventory + PMT status          :p1j, 2026-07-05, 3d

    section Week 2 - Processing & Output
    Tax estimation templates                    :p2a, 2026-07-08, 3d
    Entity comparison model                     :p2b, 2026-07-09, 2d
    Scorecard generator + Claude AI             :p2c, 2026-07-08, 3d
    Meeting agenda generator + Slides           :p2d, 2026-07-10, 2d
    Karbon task creation + notifications        :p2e, 2026-07-10, 2d
    Fathom integration + action items           :p2f, 2026-07-11, 2d
    Reclassification engine (propose-approve-apply) :p2g, 2026-07-08, 3d
    Virtual rules engine                        :p2h, 2026-07-09, 3d
    Blue J research memo integration            :p2i, 2026-07-10, 2d
    Approval gates + payment reminders          :p2j, 2026-07-11, 2d
    Run log + Looker Studio dashboard           :p2k, 2026-07-11, 2d
    Tax strategy screener + strategy library    :p2l, 2026-07-08, 4d
    QBO close and hygiene report                :p2m, 2026-07-09, 2d
    Meeting brief compiler (9 sections)         :p2n, 2026-07-11, 3d
    Deck generator (Slides default, Gamma optional) :p2o, 2026-07-12, 2d
    Preparer input prompt (T-48h email)         :p2p, 2026-07-12, 1d

    section Week 3 - Testing & Handoff
    Sandbox testing all scenarios               :p3a, 2026-07-15, 3d
    Documentation and training                  :p3b, 2026-07-15, 2d
    Production import and validation            :p3c, 2026-07-17, 2d
    Support period                              :p3d, 2026-07-18, 2d
```

### 12.2 Phase Details

| Phase | Duration | Cost | Dependencies |
|-------|----------|------|-------------|
| 1. Foundation & Data Collection | Week 1 | Developer cost (+ $0 internal setup) | None |
| 2. Processing & Output | Week 2 | Developer cost | Phase 1 |
| 3. Testing & Handoff | Week 3 | Developer cost + internal time | Phase 2 |
| **Total** | **~3 weeks (testing in the final week)** | | |

---

## 13. SOFTWARE INTEGRATION MAP

### 13.1 Full Integration Diagram

```mermaid
flowchart TD
    subgraph ORCHESTRATION["ORCHESTRATION (n8n)"]
        N8N[n8n Workflow Engine]
    end

    subgraph TRIGGERS["TRIGGERS"]
        GCAL[Google Calendar]
        GDRIVE_T[Google Drive<br/>File Watch]
    end

    subgraph DATA_SOURCES["DATA SOURCES (API)"]
        QBO[QuickBooks Online]
        XERO[Xero]
        KARBON_S[Karbon]
    end

    subgraph OFFLINE["MANUAL / OFFLINE SOURCES"]
        PAYROLL_SW[Payroll Software<br/>e.g. Rippling / Gusto / ADP<br/>Manual pay stub download]
    end

    subgraph AI["AI PROCESSING"]
        CLAUDE_S[Claude AI<br/>Anthropic API]
        CHATGPT[ChatGPT<br/>OpenAI API<br/>Backup]
        BLUEJ[Blue J Tax<br/>AI tax research<br/>cited findings<br/>used via UI]
        GAMMA_S[Gamma<br/>optional AI deck<br/>generation via API]
    end

    subgraph PRODUCTIVITY["PRODUCTIVITY"]
        GSHEETS[Google Sheets]
        GDOCS[Google Docs]
        GSLIDES[Google Slides]
        GDRIVE[Google Drive]
        GMAIL[Gmail]
    end

    subgraph TASK_MGMT["TASK MANAGEMENT"]
        KARBON_T[Karbon<br/>Work Items]
    end

    subgraph COMMUNICATION["COMMUNICATION"]
        GHL[GoHighLevel]
        FATHOM_S[Fathom]
    end

    subgraph MONITORING["OUTPUT / MONITORING"]
        LOOKER[Looker Studio<br/>free dashboard<br/>run-log + prep status]
    end

    subgraph MANUAL_TOOLS["MANUAL / REFERENCE TOOLS"]
        PROCONNECT[ProConnect<br/>Tax Returns]
        NOTEBOOK[NotebookLM<br/>Research Cross-check]
        SCRIBE_S[Scribe<br/>Process Docs]
        ANTIGRAVITY_S[Antigravity<br/>RPA Fallback]
        SAASANT[SaasAnt Transactions<br/>~$20/mo optional<br/>bulk QBO edit fallback]
    end

    GCAL --> N8N
    GDRIVE_T --> N8N

    N8N --> QBO
    N8N --> XERO
    N8N --> KARBON_S

    PAYROLL_SW -.->|Manual download<br/>+ upload| GDRIVE

    N8N --> CLAUDE_S
    N8N --> CHATGPT
    N8N -->|Optional deck path| GAMMA_S
    BLUEJ -.->|Research findings<br/>pasted or uploaded<br/>via UI| CLAUDE_S
    NOTEBOOK -.->|Cross-check| CLAUDE_S

    N8N --> GSHEETS
    N8N --> GDOCS
    N8N --> GSLIDES
    N8N --> GDRIVE
    N8N --> GMAIL

    N8N --> KARBON_T

    N8N --> GHL
    N8N --> FATHOM_S

    GSHEETS -->|Run-log sheet| LOOKER
```

### 13.2 API Requirements Summary

| System | API Type | Auth Method | n8n Node | Sandbox Available |
|--------|----------|-------------|----------|-------------------|
| Google Calendar | REST | OAuth 2.0 | Built-in | Yes (test account) |
| Google Drive | REST | OAuth 2.0 | Built-in | Yes (test account) |
| Google Sheets | REST | OAuth 2.0 | Built-in | Yes (test account) |
| Google Docs | REST | OAuth 2.0 | Built-in | Yes (test account) |
| Google Slides | REST | OAuth 2.0 | HTTP Request | Yes (test account) |
| Gmail | REST | OAuth 2.0 | Built-in | Yes (test account) |
| QuickBooks Online | REST | OAuth 2.0 | Built-in | Yes (developer.intuit.com) |
| Xero | REST | OAuth 2.0 | Built-in | Yes (Xero demo company) |
| Payroll software (e.g. Rippling/Gusto/ADP) | None — manual/offline | N/A | N/A — pay stubs downloaded and uploaded to Google Drive by the team | N/A |
| Karbon (incl. Client Requests) | REST | API Key | HTTP Request | Contact Karbon |
| Claude AI | REST | API Key | Built-in | Yes (same API) |
| ChatGPT | REST | API Key | Built-in | Yes (same API) |
| Blue J Tax | Manual/limited — used via UI | Blue J login | N/A — research findings pasted/uploaded and fed to Claude for the memo | N/A |
| Looker Studio (free) | Native Google Sheets connector (no n8n API needed) | Google account | N/A — dashboard reads the run-log Sheet directly | Yes (test account) |
| SaasAnt Transactions (~$20/mo, optional) | File-based bulk import/export for QBO | SaasAnt login + QBO connect | N/A — optional fallback for bulk QBO edits | Trial available |
| GoHighLevel | REST | API Key | HTTP Request | Yes (test account) |
| Fathom | REST | API Key | HTTP Request | Contact Fathom |
| Gamma (optional — AI deck generation) | REST | API Key | HTTP Request | API access on paid plan |

**Compliance note (v2.0):** the new intelligence ingestion — client email
threads and tax return data — is processed entirely within firm-controlled
systems (Karbon, the firm's Google Workspace, and the firm's own AI API
accounts). No client emails or tax returns flow through third-party
development environments.

---

## 14. APPENDIX

### 14.1 Complete System Flow — Single Diagram

```mermaid
flowchart TD
    START([48 hours two days<br/>before Quarterly Meeting]) --> TRIGGER[Google Calendar<br/>Trigger fires]

    TRIGGER --> LOOKUP[Look up client<br/>in Profile Matrix]

    LOOKUP --> PARALLEL_COLLECT

    subgraph PARALLEL_COLLECT["PARALLEL DATA COLLECTION & INGESTION"]
        direction TB

        K[KARBON<br/>Open items +<br/>completed since<br/>last meeting]

        F_CHECK{Accounting<br/>access?}
        F_CHECK -->|API| F_API[Pull QBO/Xero<br/>reports via API]
        F_CHECK -->|No API| F_EMAIL[Karbon client request<br/>auto-reminders<br/>email fallback]

        P_CHECK{Has<br/>payroll?}
        P_CHECK -->|Yes| P_MANUAL[Manual: team downloads<br/>+ uploads pay stubs<br/>AI parses uploaded stub]
        P_CHECK -->|None| P_SKIP[Flag distributions<br/>only]

        C_DIGEST[Comms digest<br/>emails since<br/>last meeting]
        T_RECAP[Last-meeting recap<br/>transcript feed-forward]
        T_DOCS[Tax document<br/>intelligence<br/>Drive tax folder]
        F_INV[Client file inventory<br/>+ PMT schedule status]
        K_IN[Preparer input prompt<br/>email Karen T-48h<br/>non-blocking, T-24h cutoff]
    end

    PARALLEL_COLLECT --> DATA_READY{All data<br/>available?}

    DATA_READY -->|Yes| PROCESS
    DATA_READY -->|Partial| PROCESS
    DATA_READY -->|Waiting| DRIVE_WATCH[Set Drive watch<br/>Resume when<br/>docs uploaded]
    DRIVE_WATCH -->|Files arrive| PARSE_DOCS[Claude AI<br/>parses documents]
    PARSE_DOCS --> PROCESS

    subgraph PROCESS["AI PROCESSING + CALCULATIONS"]
        direction TB
        TAX[Tax Estimation<br/>Engine<br/>Google Sheets]
        COMPARE[Entity Comparison<br/>With vs Without<br/>C-Corp]
        SCORECARD[Client Scorecard<br/>4 metrics +<br/>AI narrative]
        RESEARCH[Tax Research Memo<br/>Blue J findings +<br/>Claude cited memo]
        SCREEN[Tax Strategy Screener<br/>~35-strategy library<br/>ranked by savings]
        BOOKS[QBO Close & Hygiene<br/>Books Health report]
    end

    PROCESS --> GENERATE

    subgraph GENERATE["DOCUMENT GENERATION"]
        direction TB
        BRIEF_GEN[Meeting Brief<br/>9-section Google Doc<br/>agenda as component]
        DECK_GEN[Presentation Deck<br/>Google Slides default<br/>Gamma optional]
        TASKS_GEN[Task Delegation<br/>Karbon work items]
    end

    GENERATE --> SAVE_ALL[Save everything<br/>to Google Drive<br/>client folder]

    SAVE_ALL --> NOTIFY_PREP[Email notification<br/>to preparer<br/>Prep is ready]

    NOTIFY_PREP --> HUMAN_REVIEW[HUMAN REVIEW<br/>15-20 minutes<br/>Verify and customize]

    HUMAN_REVIEW --> GATE{One-click gate<br/>Approve /<br/>Request Changes}
    GATE -->|Request Changes| PROCESS
    GATE -->|Approve| CLIENT_MEETING[CLIENT MEETING<br/>Zoom/Teams]

    CLIENT_MEETING --> POST

    subgraph POST["POST-MEETING AUTOMATION"]
        direction TB
        FATHOM_PULL[Fathom transcript<br/>auto-detected]
        ACTION_EXTRACT[Claude AI extracts<br/>action items]
        TASK_CREATE[Karbon work items<br/>created]
        FOLLOWUP[Client follow-up<br/>email drafted]
        KARBON_UPDATE[Karbon updated<br/>with meeting notes]
        LINK_SAVE[Transcript link saved<br/>to client profile<br/>feeds next prep]
    end

    POST --> NEXT([Ready for<br/>next quarter<br/>transcript feed-forward])
```

### 14.2 File Naming Conventions

All automated outputs follow this naming convention:

```
{ClientName}_QMP_{Quarter}{Year}_{DocumentType}.{ext}

Examples:
CandaceMyers_QMP_Q1-2026_Scorecard.xlsx
CandaceMyers_QMP_Q1-2026_TaxEstimate.xlsx
CandaceMyers_QMP_Q1-2026_MeetingBrief.docx
CandaceMyers_QMP_Q1-2026_Presentation.pptx
CandaceMyers_QMP_Q1-2026_PayrollSummary.pdf
```

### 14.3 Google Drive Folder Structure

```
Client Root Folder/
├── 2026/
│   ├── Q1/
│   │   ├── Payroll/
│   │   │   ├── Justin_PayStub_Q1-2026.pdf
│   │   │   └── Candace_PayStub_Q1-2026.pdf
│   │   ├── Financials/
│   │   │   ├── PnL_YTD_Q1-2026.csv
│   │   │   └── BalanceSheet_Q1-2026.csv
│   │   ├── Tax/
│   │   │   ├── TaxEstimate_Q1-2026.xlsx
│   │   │   └── EntityComparison_Q1-2026.xlsx
│   │   └── Meeting/
│   │       ├── Scorecard_Q1-2026.xlsx
│   │       ├── MeetingBrief_Q1-2026.docx
│   │       └── Presentation_Q1-2026.pptx
│   ├── Q2/
│   ├── Q3/
│   └── Q4/
└── Prior Years/
```

### 14.4 Future Enhancements (Optional Avenues)

These are optional avenues beyond the v2.0 scope — none are required for
the system to operate, and none change the locked decisions above. (Items
that were future avenues in v1.1 and are now in scope — client email
review, transcript feed-forward, tax return mining, strategy screening,
the meeting brief, and deck generation — have been promoted into
Sections 3-5 and removed from this list.)

- **Dedicated payroll intake mailbox.** Clients email their pay stubs to
  a dedicated address; n8n parses and files them automatically into the
  client's Drive folder. Still no payroll logins or dashboard
  connections — collection remains client-driven.
- **QBO Payroll passthrough (existing connections only).** For clients
  whose payroll runs inside QBO Payroll on an already-connected QBO
  account, payslips could be pulled through that same existing QBO
  connection — no new dashboards or logins are added.
- **AI-agent connectors (MCP).** MCP connectors for QuickBooks, Gmail,
  and Google Drive would enable ad-hoc, AI-driven prep runs outside n8n
  (e.g., "re-run the scorecard for Client A with the latest QBO data").
- **Client portal.** A simple portal for clients to upload documents and
  view their scorecard between meetings.

---

*End of Comprehensive Workflow Documentation*
