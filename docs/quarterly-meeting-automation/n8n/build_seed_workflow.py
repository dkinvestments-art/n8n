#!/usr/bin/env python3
"""Builds the n8n seed workflow JSON that creates the automation Google Sheets
in Karen's Astute Advisors Drive. Embeds each CSV as base64 so no quoting can
break, and each Code node parses it into rows for the Google Sheets append.

Run:  python3 build_seed_workflow.py
Emits: Astute-Seed-Automation-Sheets.workflow.json
"""
import base64, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "strategy-library", "Strategy-Library.csv")

DATASETS = [
    {"key": "Library", "title": "Tax Strategy Library",   "csv": LIB},
    {"key": "Status",  "title": "Client Strategy Status", "csv": os.path.join(HERE, "Client-Strategy-Status.csv")},
    {"key": "Profile", "title": "Client Profile Matrix",  "csv": os.path.join(HERE, "Client-Profile-Matrix.csv")},
]

SHEETS_CRED = {"googleSheetsOAuth2Api": {"id": "REPLACE_WITH_KAREN_ASTUTE_GOOGLE_CRED",
                                          "name": "Karen Astute Advisors Google"}}
DRIVE_CRED = {"googleDriveOAuth2Api": {"id": "REPLACE_WITH_KAREN_ASTUTE_GOOGLE_CRED",
                                        "name": "Karen Astute Advisors Google"}}

CODE_TEMPLATE = '''// Decodes the embedded CSV and returns one item per row for the Sheets append.
const b64 = "%s";
const csv = Buffer.from(b64, "base64").toString("utf8");
function parseCSV(text) {
  const rows = []; let i = 0, field = "", row = [], inQ = false;
  while (i < text.length) {
    const c = text[i];
    if (inQ) {
      if (c === '"') { if (text[i + 1] === '"') { field += '"'; i += 2; continue; } inQ = false; i++; continue; }
      field += c; i++; continue;
    }
    if (c === '"') { inQ = true; i++; continue; }
    if (c === ',') { row.push(field); field = ""; i++; continue; }
    if (c === '\\r') { i++; continue; }
    if (c === '\\n') { row.push(field); rows.push(row); row = []; field = ""; i++; continue; }
    field += c; i++;
  }
  if (field.length > 0 || row.length > 0) { row.push(field); rows.push(row); }
  return rows;
}
const rows = parseCSV(csv).filter(r => r.length > 1 || (r.length === 1 && r[0] !== ""));
const headers = rows.shift();
if (!rows.length) { return [{ json: Object.fromEntries(headers.map(h => [h, ""])) }]; }
return rows.map(r => {
  const o = {}; headers.forEach((h, idx) => o[h] = r[idx] !== undefined ? r[idx] : ""); return { json: o };
});
'''

def rl_id(expr):
    return {"__rl": True, "mode": "id", "value": expr}

nodes = []
connections = {}

def add(node):
    nodes.append(node)

def connect(src, dst, index=0):
    connections.setdefault(src, {"main": [[]]})
    connections[src]["main"][0].append({"node": dst, "type": "main", "index": index})

# 1. Manual trigger
add({"parameters": {}, "id": "trigger", "name": "Run once to seed sheets",
     "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [-40, 400]})

# 2. Config
add({"parameters": {"assignments": {"assignments": [
        {"id": "a1", "name": "automationsFolderId", "type": "string",
         "value": "PASTE_ASTUTE_AUTOMATIONS_FOLDER_ID_HERE"}]}, "options": {}},
     "id": "config", "name": "Config (set Astute folder ID)",
     "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [180, 400]})
connect("Run once to seed sheets", "Config (set Astute folder ID)")

y = 40
for d in DATASETS:
    with open(d["csv"], "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    k, title = d["key"], d["title"]
    create_name = f"Create {k} Sheet"
    move_name = f"Move {k} to Astute folder"
    code_name = f"{k} rows"
    append_name = f"Append {k} rows"
    sid = f"={{{{ $('{create_name}').first().json.spreadsheetId }}}}"

    add({"parameters": {"resource": "spreadsheet", "operation": "create",
            "title": title, "sheetsUi": {"sheetValues": [{"title": "Sheet1"}]}, "options": {}},
         "id": f"create{k}", "name": create_name, "type": "n8n-nodes-base.googleSheets",
         "typeVersion": 4.5, "position": [420, y], "credentials": SHEETS_CRED})

    add({"parameters": {"resource": "file", "operation": "move",
            "fileId": rl_id(sid),
            "driveId": {"__rl": True, "mode": "list", "value": "My Drive"},
            "folderId": rl_id("={{ $('Config (set Astute folder ID)').first().json.automationsFolderId }}")},
         "id": f"move{k}", "name": move_name, "type": "n8n-nodes-base.googleDrive",
         "typeVersion": 3, "position": [660, y], "credentials": DRIVE_CRED})

    add({"parameters": {"jsCode": CODE_TEMPLATE % b64},
         "id": f"code{k}", "name": code_name, "type": "n8n-nodes-base.code",
         "typeVersion": 2, "position": [900, y]})

    add({"parameters": {"resource": "sheet", "operation": "append",
            "documentId": rl_id(sid),
            "sheetName": {"__rl": True, "mode": "list", "value": "gid=0", "cachedResultName": "Sheet1"},
            "mappingMode": "autoMapInputData", "options": {}},
         "id": f"append{k}", "name": append_name, "type": "n8n-nodes-base.googleSheets",
         "typeVersion": 4.5, "position": [1140, y], "credentials": SHEETS_CRED})

    connect("Config (set Astute folder ID)", create_name)
    connect(create_name, move_name)
    connect(move_name, code_name)
    connect(code_name, append_name)
    y += 240

workflow = {
    "name": "Astute — Seed Automation Sheets (run once)",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1"},
    "meta": {"description": "Creates the Tax Strategy Library, Client Strategy Status, "
             "and Client Profile Matrix Google Sheets in Karen's Astute Advisors Drive. "
             "Select Karen's Astute Google credential on all Google nodes and paste the "
             "Astute Automations folder ID into the Config node before running."}
}

out = os.path.join(HERE, "Astute-Seed-Automation-Sheets.workflow.json")
with open(out, "w") as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)
print(f"Wrote {out}")
print(f"Nodes: {len(nodes)}")
