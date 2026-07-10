#!/usr/bin/env python3
"""Builds the main Quarterly Meeting Prep pipeline as an importable n8n
workflow SCAFFOLD. The trigger, calendar routing, profile lookup, control
flow, approval gate, and output wiring are real; each ingestion / AI step is
a labeled node (HTTP Request / Code / Google node) that the developer
completes with the specific API call and prompt. Sticky notes document each.

All Google/Gmail nodes carry an Astute Advisors credential placeholder so the
whole pipeline runs under Karen's Astute account (see ../DATA-GOVERNANCE.md).

Run:  python3 build_main_pipeline.py
Emits: Astute-Quarterly-Prep-Pipeline.workflow.json
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Astute-Quarterly-Prep-Pipeline.workflow.json")

GOOGLE_SHEETS_CRED = {"googleSheetsOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google"}}
GOOGLE_DOCS_CRED = {"googleDocsOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google"}}
GOOGLE_DRIVE_CRED = {"googleDriveOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google"}}
GCAL_CRED = {"googleCalendarOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google"}}
GMAIL_CRED = {"gmailOAuth2": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Gmail"}}

nodes, connections = [], {}

def add(node): nodes.append(node); return node["name"]

def wire(src, dst, src_out=0):
    c = connections.setdefault(src, {"main": []})
    while len(c["main"]) <= src_out: c["main"].append([])
    c["main"][src_out].append({"node": dst, "type": "main", "index": 0})

def note(name, content, x, y, w=300, h=160, color=4):
    add({"parameters": {"content": content, "height": h, "width": w, "color": color},
         "id": "note_" + name.replace(" ", "_")[:24], "name": name,
         "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [x, y]})

def http(name, x, y, method="GET", url="=PLACEHOLDER — see sticky note"):
    return add({"parameters": {"method": method, "url": url, "options": {}},
                "id": name.replace(" ", "_")[:28], "name": name,
                "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x, y]})

def code(name, x, y, note_txt=""):
    return add({"parameters": {"jsCode": f"// {note_txt}\n// TODO (developer): implement per the Developer Requirements Spec.\nreturn $input.all();"},
                "id": name.replace(" ", "_")[:28], "name": name,
                "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x, y]})

def noop(name, x, y):
    return add({"parameters": {}, "id": name.replace(" ", "_")[:28], "name": name,
                "type": "n8n-nodes-base.noOp", "typeVersion": 1, "position": [x, y]})

X = 0
def col(step=240):
    global X; X += step; return X

# ---------- PHASE A: TRIGGER & ROUTING ----------
note("① Trigger & Routing",
     "Runs on a schedule, finds meetings ~48h out tagged 'Quarterly', and loads that client's profile "
     "(Karbon + the Client Profile Matrix sheet). All Google nodes use Karen's Astute credential.",
     -40, -220, 460, 150, color=5)

trig = add({"parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 6}]}},
            "id": "trigger", "name": "Every 6 hours",
            "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [X, 0]})

cal = add({"parameters": {"resource": "event", "operation": "getAll", "returnAll": True,
            "options": {"timeMin": "={{ $now.plus(24, 'hours').toISO() }}",
                        "timeMax": "={{ $now.plus(72, 'hours').toISO() }}"}},
           "id": "calendar", "name": "Get calendar events (24-72h)",
           "type": "n8n-nodes-base.googleCalendar", "typeVersion": 1, "position": [col(), 0],
           "credentials": GCAL_CRED})
wire(trig, cal)

filt = add({"parameters": {"conditions": {"options": {"caseSensitive": False},
             "conditions": [{"leftValue": "={{ $json.summary }}", "rightValue": "Quarterly",
                             "operator": {"type": "string", "operation": "contains"}}]}},
            "id": "filter", "name": "Only 'Quarterly' meetings",
            "type": "n8n-nodes-base.filter", "typeVersion": 2, "position": [col(), 0]})
wire(cal, filt)

lookup = add({"parameters": {"resource": "sheet", "operation": "read",
               "documentId": {"__rl": True, "mode": "id", "value": "=PASTE_CLIENT_PROFILE_MATRIX_SHEET_ID"},
               "sheetName": {"__rl": True, "mode": "list", "value": "gid=0"},
               "filtersUI": {"values": [{"lookupColumn": "client_name",
                             "lookupValue": "={{ $json.attendeesClientName || $json.summary }}"}]}, "options": {}},
              "id": "profile", "name": "Lookup Client Profile",
              "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": [col(), 0],
              "credentials": GOOGLE_SHEETS_CRED})
wire(filt, lookup)

ctx = add({"parameters": {"assignments": {"assignments": [
            {"id": "c1", "name": "client_id", "type": "string", "value": "={{ $json.client_id }}"},
            {"id": "c2", "name": "client_name", "type": "string", "value": "={{ $json.client_name }}"},
            {"id": "c3", "name": "last_meeting_date", "type": "string", "value": "={{ $json.last_meeting_date }}"}]},
            "options": {}},
           "id": "context", "name": "Build Context",
           "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [col(), 0]})
wire(lookup, ctx)

# ---------- PHASE B: INGESTION ----------
note("② Ingestion — everything since the last meeting",
     "Scaffold runs these in sequence for clarity. In production, fan them out as PARALLEL branches "
     "off 'Build Context' and re-join with a Merge before Phase ③. Each node is a placeholder: wire the "
     "real API call + Claude prompt per the Developer Requirements Spec (Sub-Workflows 1, 12-15, 18).",
     -40, 200, 620, 170, color=5)

prev = ctx
ingestion = [
    ("Karbon: work items (open + completed)", "http", "Karbon API — open items + items completed since last_meeting_date"),
    ("Client emails since last meeting", "http", "Karbon communications API (fallback: Gmail search from/to client)"),
    ("AI: email digest", "code", "Claude — commitments, questions, changes, unresolved threads"),
    ("Fathom: last meeting transcript", "http", "Fathom API — fetch prior transcript via last_meeting_transcript_link"),
    ("AI: transcript recap (Done/Pending/Blocked)", "code", "Claude — promises made, cross-referenced vs Karbon work items"),
    ("QBO: financials + aging + uncategorized", "http", "QBO API — P&L, Balance Sheet, A/R + A/P aging, uncategorized txns, recon status"),
    ("AI: books health report", "code", "Claude — month-end close status, hygiene flags, proposed categorizations"),
    ("Drive: tax documents", "http", "Google Drive — search drive_tax_folder for returns + prior plans"),
    ("AI: tax position extract", "code", "Claude — AGI, rates, carryforwards, elections, safe harbor, estimates paid"),
    ("Drive: client files + PMT status", "http", "Google Drive — full folder inventory + PMT schedule status"),
    ("Gmail: preparer input prompt", "gmail", "Email Karen 'any updates?' at T-48h; non-blocking, proceed at T-24h"),
]
y = 420
for i, (nm, kind, desc) in enumerate(ingestion):
    x = 240 + (i % 6) * 240
    yy = y + (i // 6) * 170
    if kind == "http": n = http(nm, x, yy)
    elif kind == "code": n = code(nm, x, yy, desc)
    elif kind == "gmail":
        n = add({"parameters": {"resource": "message", "operation": "send",
                  "sendTo": "=PASTE_KAREN_EMAIL", "subject": "=Prepping for {{ $json.client_name }} — any updates?",
                  "message": "Any updates, concerns, or topics to include for this client's quarterly meeting? Reply or leave blank.",
                  "options": {}}, "id": nm.replace(" ", "_")[:28], "name": nm,
                 "type": "n8n-nodes-base.gmail", "typeVersion": 2, "position": [x, yy], "credentials": GMAIL_CRED})
    wire(prev, n)
    prev = n

# ---------- PHASE C: AI PROCESSING ----------
note("③ Analysis",
     "Screener reads the Tax Strategy Library sheet and evaluates every Firm-Approved strategy against the "
     "assembled client data. Estimate/comparison/scorecard follow. Wire each to the Claude API (or n8n AI nodes).",
     -40, 760, 560, 150, color=5)

lib = add({"parameters": {"resource": "sheet", "operation": "read",
            "documentId": {"__rl": True, "mode": "id", "value": "=PASTE_TAX_STRATEGY_LIBRARY_SHEET_ID"},
            "sheetName": {"__rl": True, "mode": "list", "value": "gid=0"}, "options": {}},
           "id": "readlib", "name": "Read Strategy Library",
           "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": [240, 940],
           "credentials": GOOGLE_SHEETS_CRED})
wire(prev, lib)

screener = code("AI: Tax Strategy Screener", 480, 940,
                "Claude — screen Firm-Approved strategies vs client data; filter implemented/rejected; rank by est. savings; top 2-3 -> Blue J memo")
wire(lib, screener)
estimate = code("AI: Tax estimate + entity comparison", 720, 940,
                "Claude/Sheets — quarterly estimates, safe harbor, with/without C-Corp comparison")
wire(screener, estimate)
scorecard = code("AI: Scorecard + financial review", 960, 940,
                 "Claude — 4 metrics + CFO talking points framed in the tax story")
wire(estimate, scorecard)

# ---------- PHASE D: BRIEF & APPROVAL ----------
note("④ Meeting Brief & Approval Gate",
     "Compile the 9-section Meeting Brief (Google Doc), notify Karen with an Approve link, and WAIT. "
     "Nothing client-facing is produced until she approves (resume webhook).",
     -40, 1120, 560, 150, color=6)

brief = add({"parameters": {"operation": "create", "title": "=Meeting Brief — {{ $json.client_name }} — {{ $now.toFormat('yyyy-MM-dd') }}",
              "folderId": {"__rl": True, "mode": "id", "value": "=PASTE_ASTUTE_CLIENT_FOLDER_ID"}},
             "id": "brief", "name": "Create Meeting Brief (Doc)",
             "type": "n8n-nodes-base.googleDocs", "typeVersion": 2, "position": [240, 1300],
             "credentials": GOOGLE_DOCS_CRED})
wire(scorecard, brief)

notify = add({"parameters": {"resource": "message", "operation": "send", "sendTo": "=PASTE_KAREN_EMAIL",
               "subject": "=Prep ready — {{ $json.client_name }} — approve to release", "emailType": "html",
               "message": "=Brief: {{ $json.documentUrl }}<br><br>Approve: {{ $execution.resumeUrl }}", "options": {}},
              "id": "notify", "name": "Notify Karen (Approve link)",
              "type": "n8n-nodes-base.gmail", "typeVersion": 2, "position": [480, 1300], "credentials": GMAIL_CRED})
wire(brief, notify)

gate = add({"parameters": {"resume": "webhook", "options": {}},
            "id": "gate", "name": "APPROVAL GATE (wait)",
            "type": "n8n-nodes-base.wait", "typeVersion": 1.1, "position": [720, 1300],
            "webhookId": "astute-prep-approval"})
wire(notify, gate)

approved = add({"parameters": {"conditions": {"options": {"caseSensitive": False},
                 "conditions": [{"leftValue": "={{ $json.approved }}", "rightValue": "true",
                                 "operator": {"type": "string", "operation": "equals"}}]}},
                "id": "approved", "name": "Approved?",
                "type": "n8n-nodes-base.if", "typeVersion": 2, "position": [960, 1300]})
wire(gate, approved)

# ---------- PHASE E: OUTPUTS (only after approval) ----------
note("⑤ Outputs (after approval)",
     "Generate the deck (Slides or Gamma), create Karbon work items, schedule estimated-payment reminders, "
     "and append the run log. The 'not approved' path returns to revise the brief.",
     -40, 1520, 620, 150, color=5)

deck = http("Generate deck (Slides/Gamma API)", 240, 1700, method="POST")
wire(approved, deck, src_out=0)  # true branch
tasks = http("Karbon: create work items", 480, 1700, method="POST")
wire(deck, tasks)
reminders = code("Schedule payment reminders", 720, 1700,
                 "Create scheduled reminders before each federal/CA estimated-payment due date (amounts + EFTPS / CA FTB Web Pay links)")
wire(tasks, reminders)
runlog = add({"parameters": {"resource": "sheet", "operation": "append",
               "documentId": {"__rl": True, "mode": "id", "value": "=PASTE_RUN_LOG_SHEET_ID"},
               "sheetName": {"__rl": True, "mode": "list", "value": "gid=0"},
               "mappingMode": "autoMapInputData", "options": {}},
              "id": "runlog", "name": "Append run log",
              "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": [960, 1700],
              "credentials": GOOGLE_SHEETS_CRED})
wire(reminders, runlog)

revise = noop("Revise brief & re-notify", 240, 1860)
wire(approved, revise, src_out=1)  # false branch
wire(revise, brief)

note("⚠ Scaffold — read me",
     "This is an importable BLUEPRINT of the v2.0 pipeline. Real: trigger, calendar routing, profile lookup, "
     "control flow, approval gate, output wiring. Placeholders (marked TODO / 'PLACEHOLDER'): each ingestion "
     "and AI node — wire the specific API call + Claude prompt per the Developer Requirements Spec. Replace all "
     "PASTE_* ids and select Karen's Astute credential on every Google/Gmail node. Validate against your n8n "
     "version before production.",
     -40, -420, 900, 170, color=3)

wf = {"name": "Astute — Quarterly Prep Pipeline (v2.0 scaffold)", "nodes": nodes,
      "connections": connections, "settings": {"executionOrder": "v1"},
      "meta": {"description": "Importable scaffold of the quarterly meeting prep pipeline. "
               "Runs under Karen's Astute Advisors credentials. Complete the ingestion/AI placeholder "
               "nodes per the Developer Requirements Specification."}}

with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
print(f"Wrote {OUT}")
print(f"Nodes: {len(nodes)} ({sum(1 for n in nodes if n['type']=='n8n-nodes-base.stickyNote')} sticky notes)")
