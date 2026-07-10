#!/usr/bin/env python3
"""Generates the operational workflows + the master orchestrator.

- QMP-00b Operations Sheet Seeder (creates the QMP Operations spreadsheet w/ all tabs)
- QMP-08  Post-Meeting (Fathom -> actions -> Karbon -> Meeting History -> profile update)
- QMP-09a Reclassification Propose (QBO uncategorized -> Claude -> Review tab)
- QMP-09b Reclassification Apply (approved rows -> QBO update + audit log)
- QMP-10  Virtual Rules Engine (Rules tab -> QBO apply; unmatched -> Proposed Rules)
- QMP-11  Payment Reminders (Payment Schedule tab -> Gmail before due dates)
- QMP-16  Preparer Input Capture (Gmail reply -> Preparer Notes tab)
- QMP-18  Books Health (sub-workflow variant of the worked example, ctx-driven)
- QMP-MASTER Quarterly Prep Orchestrator

Run:  python3 build_ops_workflows.py
"""
from qmp_lib import (WF, PH, P, exec_trigger, manual_trigger, schedule_trigger, code, http,
                     sheets_read, sheets_append, sheets_update, gmail_send, qbo_get,
                     GOOGLE_SHEETS_CRED, GOOGLE_DOCS_CRED, GMAIL_CRED, GCAL_CRED,
                     KARBON_CRED, FATHOM_CRED, QBO_CRED)
import json

OPS_TABS = {
    "Run Log": ["run_date", "client_id", "client_name", "meeting_date", "status", "brief_url", "deck_url", "flags"],
    "Meeting History": ["client_id", "client_name", "meeting_date", "transcript_link", "summary", "action_items", "strategies_discussed"],
    "Preparer Notes": ["client_name", "meeting_date", "notes", "received_at"],
    "Payment Schedule": ["client_id", "client_name", "client_email", "quarter", "due_date", "federal", "state", "approved", "reminded", "notes"],
    "Reclassification Review": ["client_id", "realm_id", "txn_id", "txn_type", "date", "description", "amount", "proposed_account", "proposed_account_id", "confidence", "approved", "applied", "approved_by"],
    "Reclass Audit Log": ["applied_at", "client_id", "txn_id", "old_account", "new_account", "approved_by"],
    "Rules": ["rule_id", "client_id", "match_field", "contains", "target_account", "target_account_id", "active"],
    "Proposed Rules": ["proposed_at", "client_id", "pattern", "occurrences", "status"],
    "Proposed Strategies": ["proposed_at", "source", "strategy_name", "description", "status"],
}

BOOKS_SYSTEM = (
    "You are a CPA's assistant producing a \"Books Health\" section for a quarterly "
    "meeting brief. You are given QuickBooks data: A/R aging, A/P aging, balance sheet, "
    "and a list of recent transactions. Summarize the state of the books plainly. Flag: "
    "stale or large uncategorized items, aged receivables or payables, negative or unusual "
    "balances, and anything that would make the financials unreliable for tax projection. "
    "Propose a likely category for each uncategorized transaction, but mark each proposal "
    "as needs_review=true — a human approves before anything is applied. Do not invent "
    "transactions. Output only the JSON schema.")
BOOKS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["close_status", "summary", "flags", "uncategorized_proposals", "ar_summary", "ap_summary"],
    "properties": {
        "close_status": {"type": "string", "enum": ["clean", "minor_issues", "needs_attention", "not_reliable"]},
        "summary": {"type": "string"},
        "flags": {"type": "array", "items": {"type": "string"}},
        "uncategorized_proposals": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["transaction", "amount", "proposed_category", "confidence", "needs_review"],
            "properties": {"transaction": {"type": "string"}, "amount": {"type": ["number", "null"]},
                            "proposed_category": {"type": "string"},
                            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                            "needs_review": {"type": "boolean"}}}},
        "ar_summary": {"type": "string"}, "ap_summary": {"type": "string"}}}

def claude_http(name, x, y):
    return http(name, "https://api.anthropic.com/v1/messages", x, y, method="POST",
                cred_type="anthropicApi", headers=[("anthropic-version", "2023-06-01")],
                json_body="={{ JSON.stringify($json.payload) }}")

# ------------------------------------------------------- QMP-00b ops sheet seed
wf = WF("QMP-00b Seed Operations Sheet",
        "One-time: creates the 'QMP Operations' spreadsheet with all operational tabs and "
        "header rows (Run Log, Meeting History, Preparer Notes, Payment Schedule, "
        "Reclassification Review, Reclass Audit Log, Rules, Proposed Rules, Proposed "
        "Strategies). Paste the returned spreadsheetId wherever PASTE_QMP_OPERATIONS_SHEET_ID appears.")
t = wf.add(manual_trigger("Run once to seed ops sheet"))
build = wf.add(code("Build spreadsheet body",
    "const tabs = " + json.dumps(OPS_TABS) + ";\n"
    "const sheets = Object.entries(tabs).map(([title, headers]) => ({\n"
    "  properties: { title },\n"
    "  data: [{ rowData: [{ values: headers.map(h => ({ userEnteredValue: { stringValue: h } })) }] }]\n"
    "}));\n"
    "return [{ json: { payload: { properties: { title: 'QMP Operations' }, sheets } } }];\n", 220, 300))
create = wf.add(http("Sheets: create QMP Operations", "https://sheets.googleapis.com/v4/spreadsheets",
    440, 300, method="POST", cred_type="googleSheetsOAuth2Api",
    json_body="={{ JSON.stringify($json.payload) }}"))
wf.nodes[-1]["credentials"] = GOOGLE_SHEETS_CRED
out = wf.add(code("Return spreadsheet id",
    "return [{ json: { spreadsheetId: $json.spreadsheetId, url: $json.spreadsheetUrl } }];\n", 660, 300))
wf.chain(t, build, create, out)
wf.write("QMP-00b-Seed-Operations-Sheet.workflow.json")

# ------------------------------------------------------------ QMP-18 books sub
wf = WF("QMP-18 Books Health (sub)",
        "Sub-workflow variant of the Books Health worked example: A/R + A/P aging, Balance "
        "Sheet, recent transactions -> Claude Books Health. Returns ctx + books_health.")
t = wf.add(exec_trigger())
ar = wf.add(qbo_get("QBO: A/R aging", "/reports/AgedReceivables", 220, 300))
ap = wf.add(qbo_get("QBO: A/P aging", "/reports/AgedPayables", 440, 300))
txn = wf.add(qbo_get("QBO: recent transactions", "/query", 660, 300,
                     qs=[("query", "SELECT * FROM Purchase ORDERBY TxnDate DESC MAXRESULTS 50")]))
build = wf.add(code("Build request: books health",
    "const ctx = $('Input').first().json;\n"
    "const userContent = 'Client: ' + ctx.client_name +\n"
    "  '\\n\\n--- A/R AGING ---\\n' + JSON.stringify($('QBO: A/R aging').first().json) +\n"
    "  '\\n\\n--- A/P AGING ---\\n' + JSON.stringify($('QBO: A/P aging').first().json) +\n"
    "  '\\n\\n--- BALANCE SHEET ---\\n' + JSON.stringify(ctx.financials?.balance_sheet ?? {}) +\n"
    "  '\\n\\n--- RECENT TRANSACTIONS ---\\n' + JSON.stringify($('QBO: recent transactions').first().json);\n"
    "const payload = { model: 'claude-opus-4-8', max_tokens: 8000,\n"
    "  system: " + json.dumps(BOOKS_SYSTEM) + ",\n"
    "  messages: [{ role: 'user', content: userContent }],\n"
    "  output_config: { effort: 'high', format: { type: 'json_schema', schema: " + json.dumps(BOOKS_SCHEMA) + " } } };\n"
    "return [{ json: { payload } }];\n", 880, 300))
claude = wf.add(claude_http("Claude: books health", 1100, 300))
parse = wf.add(code("Parse: books health",
    "const ctx = $('Input').first().json;\n"
    "const text = $json.content?.[0]?.text ?? '{}';\n"
    "let out; try { out = JSON.parse(text); } catch (e) { out = { parse_error: true, raw: text }; }\n"
    "return [{ json: { ...ctx, books_health: out } }];\n", 1320, 300))
wf.chain(t, ar, ap, txn, build, claude, parse)
wf.write("QMP-18-Books-Health-Sub.workflow.json")

# -------------------------------------------------------------- QMP-16 capture
wf = WF("QMP-16 Preparer Input Capture",
        "Watches Karen's Astute Gmail for replies with subject 'Prep input: <client>' and "
        "stores them in the Preparer Notes tab. Non-blocking: the master proceeds with or "
        "without notes.")
t = wf.add({"parameters": {"pollTimes": {"item": [{"mode": "everyHour"}]}, "simple": True,
                            "filters": {"q": "subject:\"Prep input:\""}, "options": {}},
            "id": "gmailtrig", "name": "Gmail: watch for prep input",
            "type": "n8n-nodes-base.gmailTrigger", "typeVersion": 1.2, "position": [0, 300],
            "credentials": GMAIL_CRED})
parse = wf.add(code("Parse prep input",
    "return $input.all().map(i => {\n"
    "  const m = i.json;\n"
    "  const subject = m.subject ?? m.Subject ?? '';\n"
    "  const client = (subject.split('Prep input:')[1] ?? '').trim();\n"
    "  const notes = (m.textPlain ?? m.snippet ?? '').slice(0, 4000);\n"
    "  return { json: { client_name: client, meeting_date: '', notes, received_at: new Date().toISOString() } };\n"
    "}).filter(i => i.json.client_name);\n", 220, 300))
append = wf.add(sheets_append("Append Preparer Notes", PH["OPS_SHEET"], "Preparer Notes", 440, 300))
wf.chain(t, parse, append)
wf.write("QMP-16-Preparer-Input-Capture.workflow.json")

# --------------------------------------------------------------- QMP-08 postmtg
wf = WF("QMP-08 Post-Meeting Processing",
        "Every 2h: fetches recent Fathom meetings, matches them to clients, extracts action "
        "items + summary with Claude, creates Karbon work items for firm actions, writes "
        "Meeting History (feeds next quarter's recap), proposes discussed strategies to the "
        "library intake, updates the client profile row, and drafts the client follow-up email.")
t = wf.add(schedule_trigger("Every 2 hours", hours=2))
profiles = wf.add(sheets_read("Read client profiles", PH["PROFILE_SHEET"], "Sheet1", 220, 300))
fathom = wf.add(http("Fathom: recent meetings", "https://api.fathom.ai/external/v1/meetings",
    440, 300, cred=FATHOM_CRED,
    qs=[("created_after", "={{ $now.minus({ hours: 6 }).toISO() }}"),
        ("include_transcript", "true")]))
match = wf.add(code("Match meetings to clients",
    "const profiles = $('Read client profiles').all().map(i => i.json).filter(p => p.client_name);\n"
    "const meetings = $json.items ?? $json.meetings ?? (Array.isArray($json) ? $json : []);\n"
    "const out = [];\n"
    "for (const m of meetings) {\n"
    "  const hay = ((m.title ?? '') + ' ' + JSON.stringify(m.invitees ?? m.attendees ?? [])).toLowerCase();\n"
    "  const p = profiles.find(p => hay.includes(String(p.client_name).toLowerCase()));\n"
    "  if (!p) continue;\n"
    "  const transcript = typeof m.transcript === 'string' ? m.transcript : JSON.stringify(m.transcript ?? m.summary ?? '');\n"
    "  out.push({ json: { ...p, meeting_title: m.title ?? '', meeting_date: (m.created_at ?? '').slice(0, 10),\n"
    "    transcript_link: m.share_url ?? m.url ?? '', transcript: transcript.slice(0, 150000) } });\n"
    "}\n"
    "return out;\n", 660, 300))
build = wf.add(code("Build request: actions",
    "const payload = { model: 'claude-opus-4-8', max_tokens: 8000,\n"
    "  system: " + json.dumps(P["actions"]["system"]) + ",\n"
    "  messages: [{ role: 'user', content: 'Client: ' + $json.client_name + '\\nMeeting: ' + $json.meeting_title + ' (' + $json.meeting_date + ')\\n\\n--- TRANSCRIPT ---\\n' + $json.transcript }],\n"
    "  output_config: { effort: 'high', format: { type: 'json_schema', schema: " + json.dumps(P["actions"]["schema"]) + " } } };\n"
    "return $input.all().map(i => ({ json: { ...i.json, payload } }));\n", 880, 300))
claude = wf.add(claude_http("Claude: actions", 1100, 300))
parse = wf.add(code("Parse: actions",
    "return $input.all().map((i, idx) => {\n"
    "  const src = $('Build request: actions').all()[idx].json;\n"
    "  const text = i.json.content?.[0]?.text ?? '{}';\n"
    "  let out; try { out = JSON.parse(text); } catch (e) { out = { parse_error: true, raw: text }; }\n"
    "  return { json: { ...src, payload: undefined, extracted: out } };\n"
    "});\n", 1320, 300))
wf.chain(t, profiles, fathom, match, build, claude, parse)
# Branch 1: Meeting History
hist_row = wf.add(code("To Meeting History row",
    "return $input.all().map(i => ({ json: {\n"
    "  client_id: i.json.client_id, client_name: i.json.client_name, meeting_date: i.json.meeting_date,\n"
    "  transcript_link: i.json.transcript_link, summary: i.json.extracted?.summary ?? '',\n"
    "  action_items: JSON.stringify(i.json.extracted?.action_items ?? []),\n"
    "  strategies_discussed: JSON.stringify(i.json.extracted?.strategies_discussed ?? []) } }));\n", 1540, 100))
hist = wf.add(sheets_append("Append Meeting History", PH["OPS_SHEET"], "Meeting History", 1760, 100))
wf.wire(parse, hist_row); wf.wire(hist_row, hist)
# Branch 2: Karbon work items for firm actions
firm = wf.add(code("Split firm actions",
    "const out = [];\n"
    "for (const i of $input.all()) {\n"
    "  for (const a of (i.json.extracted?.action_items ?? []).filter(a => a.owner === 'firm')) {\n"
    "    out.push({ json: { karbon_client_id: i.json.karbon_client_id, client_name: i.json.client_name,\n"
    "      title: a.item, due: a.deadline, priority: a.priority } });\n"
    "  }\n"
    "}\n"
    "return out;\n", 1540, 260))
karbon = wf.add(http("Karbon: create work item", "https://api.karbonhq.com/v3/WorkItems",
    1760, 260, method="POST", cred=KARBON_CRED,
    json_body="={{ JSON.stringify({ Title: $json.title + ' (' + $json.client_name + ')', ClientKey: $json.karbon_client_id, DueDate: $json.due || undefined }) }}"))
wf.wire(parse, firm); wf.wire(firm, karbon)
# Branch 3: transcript-mined strategy proposals
props = wf.add(code("Split strategy proposals",
    "const out = [];\n"
    "for (const i of $input.all()) {\n"
    "  for (const s of (i.json.extracted?.strategies_discussed ?? [])) {\n"
    "    out.push({ json: { proposed_at: new Date().toISOString(), source: 'transcript:' + i.json.client_name,\n"
    "      strategy_name: String(s).slice(0, 120), description: String(s), status: 'Draft — pending Firm review' } });\n"
    "  }\n"
    "}\n"
    "return out;\n", 1540, 420))
props_app = wf.add(sheets_append("Append Proposed Strategies", PH["OPS_SHEET"], "Proposed Strategies", 1760, 420))
wf.wire(parse, props); wf.wire(props, props_app)
# Branch 4: profile update (closes the feed-forward loop)
prof_row = wf.add(code("To profile update row",
    "return $input.all().map(i => ({ json: { row_number: i.json.row_number,\n"
    "  last_meeting_date: i.json.meeting_date, last_meeting_transcript_link: i.json.transcript_link } }));\n", 1540, 580))
prof_upd = wf.add(sheets_update("Update profile row", PH["PROFILE_SHEET"], "Sheet1", 1760, 580))
wf.wire(parse, prof_row); wf.wire(prof_row, prof_upd)
# Branch 5: draft client follow-up (draft only — human sends)
draft = wf.add({"parameters": {"resource": "draft", "operation": "create",
    "subject": "=Follow-up — our meeting on {{ $json.meeting_date }}",
    "message": "={{ 'Hi ' + $json.client_name + ',\\n\\nThank you for meeting with us. Summary:\\n' + ($json.extracted?.summary ?? '') + '\\n\\nYour action items:\\n' + ($json.extracted?.action_items ?? []).filter(a => a.owner === 'client').map(a => '• ' + a.item).join('\\n') + '\\n\\nBest,\\nAstute Advisors' }}",
    "options": {"sendTo": "={{ $json.client_email }}"}},
    "id": "draftfu", "name": "Gmail: draft follow-up", "type": "n8n-nodes-base.gmail",
    "typeVersion": 2, "position": [1540, 740], "credentials": GMAIL_CRED})
wf.wire(parse, draft)
wf.write("QMP-08-Post-Meeting.workflow.json")

# --------------------------------------------------------- QMP-09a reclass propose
wf = WF("QMP-09a Reclassification Propose",
        "Weekly: for every client with QBO access, pulls recent transactions + chart of "
        "accounts, has Claude propose categorizations for uncategorized items, and writes "
        "them to the Reclassification Review tab for human approval. Nothing is applied here.")
t = wf.add(schedule_trigger("Weekly Monday 6am", cron="0 6 * * 1"))
profiles = wf.add(sheets_read("Read client profiles", PH["PROFILE_SHEET"], "Sheet1", 220, 300))
filt = wf.add(code("Clients with QBO",
    "return $input.all().filter(i => i.json.qbo_realm_id).map(i => ({ json: i.json }));\n", 440, 300))
txns = wf.add(http("QBO: recent purchases",
    "=https://quickbooks.api.intuit.com/v3/company/{{ $json.qbo_realm_id }}/query", 660, 300,
    cred_type="quickBooksOAuth2Api", headers=[("Accept", "application/json")],
    qs=[("minorversion", "73"), ("query", "SELECT * FROM Purchase ORDERBY TxnDate DESC MAXRESULTS 100")]))
wf.nodes[-1]["credentials"] = QBO_CRED
accounts = wf.add(http("QBO: chart of accounts",
    "=https://quickbooks.api.intuit.com/v3/company/{{ $('Clients with QBO').item.json.qbo_realm_id }}/query", 880, 300,
    cred_type="quickBooksOAuth2Api", headers=[("Accept", "application/json")],
    qs=[("minorversion", "73"), ("query", "SELECT Id, Name, AccountType FROM Account MAXRESULTS 500")]))
wf.nodes[-1]["credentials"] = QBO_CRED
build = wf.add(code("Build request: reclass proposals",
    "const clients = $('Clients with QBO').all().map(i => i.json);\n"
    "const txns = $('QBO: recent purchases').all().map(i => i.json);\n"
    "const accts = $('QBO: chart of accounts').all().map(i => i.json);\n"
    "const out = [];\n"
    "for (let idx = 0; idx < clients.length; idx++) {\n"
    "  const c = clients[idx];\n"
    "  const purchases = (txns[idx]?.QueryResponse?.Purchase ?? []);\n"
    "  const uncat = purchases.filter(p => (p.Line ?? []).some(l =>\n"
    "    (l.AccountBasedExpenseLineDetail?.AccountRef?.name ?? '').toLowerCase().includes('uncategor')));\n"
    "  if (!uncat.length) continue;\n"
    "  const chart = (accts[idx]?.QueryResponse?.Account ?? []).map(a => ({ id: a.Id, name: a.Name, type: a.AccountType }));\n"
    "  const compact = uncat.map(p => ({ id: p.Id, type: 'Purchase', date: p.TxnDate,\n"
    "    desc: p.EntityRef?.name ?? p.PaymentType ?? '', memo: p.PrivateNote ?? '', amount: p.TotalAmt }));\n"
    "  const payload = { model: 'claude-opus-4-8', max_tokens: 8000,\n"
    "    system: " + json.dumps(P["reclass"]["system"]) + ",\n"
    "    messages: [{ role: 'user', content: 'Client: ' + c.client_name + '\\n\\n--- CHART OF ACCOUNTS ---\\n' + JSON.stringify(chart) + '\\n\\n--- UNCATEGORIZED TRANSACTIONS ---\\n' + JSON.stringify(compact) }],\n"
    "    output_config: { effort: 'high', format: { type: 'json_schema', schema: " + json.dumps(P["reclass"]["schema"]) + " } } };\n"
    "  out.push({ json: { client_id: c.client_id, realm_id: c.qbo_realm_id, chart, payload } });\n"
    "}\n"
    "return out;\n", 1100, 300))
claude = wf.add(claude_http("Claude: reclass proposals", 1320, 300))
rows = wf.add(code("To Review rows",
    "const srcs = $('Build request: reclass proposals').all().map(i => i.json);\n"
    "const out = [];\n"
    "$input.all().forEach((i, idx) => {\n"
    "  const src = srcs[idx];\n"
    "  const text = i.json.content?.[0]?.text ?? '{}';\n"
    "  let parsed; try { parsed = JSON.parse(text); } catch (e) { parsed = { proposals: [] }; }\n"
    "  for (const pr of (parsed.proposals ?? [])) {\n"
    "    const acct = (src.chart ?? []).find(a => a.name.toLowerCase() === String(pr.proposed_account).toLowerCase());\n"
    "    out.push({ json: { client_id: src.client_id, realm_id: src.realm_id, txn_id: pr.txn_id,\n"
    "      txn_type: pr.txn_type, date: pr.date, description: pr.description, amount: pr.amount,\n"
    "      proposed_account: pr.proposed_account, proposed_account_id: acct?.id ?? '',\n"
    "      confidence: pr.confidence, approved: 'FALSE', applied: 'FALSE', approved_by: '' } });\n"
    "  }\n"
    "});\n"
    "return out;\n", 1540, 300))
append = wf.add(sheets_append("Append Review rows", PH["OPS_SHEET"], "Reclassification Review", 1760, 300))
wf.chain(t, profiles, filt, txns, accounts, build, claude, rows, append)
wf.write("QMP-09a-Reclass-Propose.workflow.json")

# ----------------------------------------------------------- QMP-09b reclass apply
wf = WF("QMP-09b Reclassification Apply",
        "Applies ONLY human-approved rows from the Reclassification Review tab to QBO "
        "(full-object update with the approved account), writes the audit log, and marks "
        "rows applied. Run manually or on a schedule after Karen approves rows.")
t = wf.add(manual_trigger("Apply approved reclassifications"))
review = wf.add(sheets_read("Read Review tab", PH["OPS_SHEET"], "Reclassification Review", 220, 300))
filt = wf.add(code("Filter approved, unapplied",
    "return $input.all().filter(i =>\n"
    "  String(i.json.approved).toUpperCase() === 'TRUE' &&\n"
    "  String(i.json.applied).toUpperCase() !== 'TRUE' &&\n"
    "  i.json.txn_id && i.json.realm_id && i.json.proposed_account_id);\n", 440, 300))
get = wf.add(http("QBO: get purchase",
    "=https://quickbooks.api.intuit.com/v3/company/{{ $json.realm_id }}/purchase/{{ $json.txn_id }}",
    660, 300, cred_type="quickBooksOAuth2Api", headers=[("Accept", "application/json")],
    qs=[("minorversion", "73")]))
wf.nodes[-1]["credentials"] = QBO_CRED
mutate = wf.add(code("Mutate account refs",
    "const rows = $('Filter approved, unapplied').all().map(i => i.json);\n"
    "return $input.all().map((i, idx) => {\n"
    "  const row = rows[idx];\n"
    "  const p = i.json.Purchase ?? i.json;\n"
    "  const oldAccount = p.Line?.[0]?.AccountBasedExpenseLineDetail?.AccountRef?.name ?? '';\n"
    "  for (const l of (p.Line ?? [])) {\n"
    "    if (l.AccountBasedExpenseLineDetail) {\n"
    "      l.AccountBasedExpenseLineDetail.AccountRef = { value: String(row.proposed_account_id), name: row.proposed_account };\n"
    "    }\n"
    "  }\n"
    "  return { json: { realm_id: row.realm_id, row_number: row.row_number, client_id: row.client_id,\n"
    "    txn_id: row.txn_id, old_account: oldAccount, new_account: row.proposed_account,\n"
    "    approved_by: row.approved_by, body: p } };\n"
    "});\n", 880, 300))
upd = wf.add(http("QBO: update purchase",
    "=https://quickbooks.api.intuit.com/v3/company/{{ $json.realm_id }}/purchase?minorversion=73",
    1100, 300, method="POST", cred_type="quickBooksOAuth2Api",
    headers=[("Accept", "application/json")], json_body="={{ JSON.stringify($json.body) }}"))
wf.nodes[-1]["credentials"] = QBO_CRED
audit_row = wf.add(code("To audit rows",
    "const rows = $('Mutate account refs').all().map(i => i.json);\n"
    "return $input.all().map((i, idx) => ({ json: { applied_at: new Date().toISOString(),\n"
    "  client_id: rows[idx].client_id, txn_id: rows[idx].txn_id, old_account: rows[idx].old_account,\n"
    "  new_account: rows[idx].new_account, approved_by: rows[idx].approved_by,\n"
    "  row_number: rows[idx].row_number } }));\n", 1320, 300))
audit = wf.add(sheets_append("Append Audit Log", PH["OPS_SHEET"], "Reclass Audit Log", 1540, 300))
mark_row = wf.add(code("To applied marks",
    "return $input.all().map(i => ({ json: { row_number: i.json.row_number, applied: 'TRUE' } }));\n", 1760, 300))
mark = wf.add(sheets_update("Mark rows applied", PH["OPS_SHEET"], "Reclassification Review", 1980, 300))
wf.chain(t, review, filt, get, mutate, upd, audit_row, audit, mark_row, mark)
wf.write("QMP-09b-Reclass-Apply.workflow.json")

# ------------------------------------------------------------- QMP-10 rules engine
wf = WF("QMP-10 Virtual Rules Engine",
        "Weekly: applies the firm's own categorization rules (Rules tab) to uncategorized "
        "QBO transactions — n8n's replacement for QBO's non-API-editable bank rules. "
        "Unmatched recurring patterns are written to Proposed Rules for review.")
t = wf.add(schedule_trigger("Weekly Monday 7am", cron="0 7 * * 1"))
rules = wf.add(sheets_read("Read Rules", PH["OPS_SHEET"], "Rules", 220, 300))
profiles = wf.add(sheets_read("Read client profiles", PH["PROFILE_SHEET"], "Sheet1", 440, 300))
clients = wf.add(code("Clients with QBO + rules",
    "const rules = $('Read Rules').all().map(i => i.json).filter(r => String(r.active).toUpperCase() === 'TRUE');\n"
    "return $input.all().filter(i => i.json.qbo_realm_id).map(i => ({ json: { ...i.json, _rules: rules.filter(r => !r.client_id || r.client_id === i.json.client_id) } }));\n", 660, 300))
txns = wf.add(http("QBO: recent purchases",
    "=https://quickbooks.api.intuit.com/v3/company/{{ $json.qbo_realm_id }}/query", 880, 300,
    cred_type="quickBooksOAuth2Api", headers=[("Accept", "application/json")],
    qs=[("minorversion", "73"), ("query", "SELECT * FROM Purchase ORDERBY TxnDate DESC MAXRESULTS 100")]))
wf.nodes[-1]["credentials"] = QBO_CRED
plan = wf.add(code("Apply rules / find patterns",
    "const clients = $('Clients with QBO + rules').all().map(i => i.json);\n"
    "const applies = []; const patterns = [];\n"
    "$input.all().forEach((i, idx) => {\n"
    "  const c = clients[idx];\n"
    "  const purchases = i.json.QueryResponse?.Purchase ?? [];\n"
    "  const counts = {};\n"
    "  for (const p of purchases) {\n"
    "    const uncat = (p.Line ?? []).some(l => (l.AccountBasedExpenseLineDetail?.AccountRef?.name ?? '').toLowerCase().includes('uncategor'));\n"
    "    if (!uncat) continue;\n"
    "    const desc = ((p.EntityRef?.name ?? '') + ' ' + (p.PrivateNote ?? '')).trim();\n"
    "    const rule = (c._rules ?? []).find(r => desc.toLowerCase().includes(String(r.contains).toLowerCase()) && r.target_account_id);\n"
    "    if (rule) {\n"
    "      applies.push({ json: { realm_id: c.qbo_realm_id, client_id: c.client_id, txn_id: p.Id,\n"
    "        target_account: rule.target_account, target_account_id: rule.target_account_id, rule_id: rule.rule_id } });\n"
    "    } else if (desc) {\n"
    "      counts[desc] = (counts[desc] ?? 0) + 1;\n"
    "      if (counts[desc] === 2) patterns.push({ json: { proposed_at: new Date().toISOString(),\n"
    "        client_id: c.client_id, pattern: desc, occurrences: 2, status: 'needs_review' } });\n"
    "    }\n"
    "  }\n"
    "});\n"
    "return [...applies.map(a => ({ json: { kind: 'apply', ...a.json } })),\n"
    "        ...patterns.map(p => ({ json: { kind: 'pattern', ...p.json } }))];\n", 1100, 300))
kind = wf.add({"parameters": {"conditions": {"options": {"caseSensitive": True},
        "conditions": [{"leftValue": "={{ $json.kind }}", "rightValue": "apply",
                         "operator": {"type": "string", "operation": "equals"}}]}},
    "id": "kindif", "name": "Apply or pattern?", "type": "n8n-nodes-base.if",
    "typeVersion": 2, "position": [1320, 300]})
get = wf.add(http("QBO: get purchase",
    "=https://quickbooks.api.intuit.com/v3/company/{{ $json.realm_id }}/purchase/{{ $json.txn_id }}",
    1540, 200, cred_type="quickBooksOAuth2Api", headers=[("Accept", "application/json")],
    qs=[("minorversion", "73")]))
wf.nodes[-1]["credentials"] = QBO_CRED
mutate = wf.add(code("Mutate per rule",
    "const rows = $('Apply or pattern?').all(0).map(i => i.json);\n"
    "return $input.all().map((i, idx) => {\n"
    "  const row = rows[idx];\n"
    "  const p = i.json.Purchase ?? i.json;\n"
    "  for (const l of (p.Line ?? [])) {\n"
    "    if (l.AccountBasedExpenseLineDetail) {\n"
    "      l.AccountBasedExpenseLineDetail.AccountRef = { value: String(row.target_account_id), name: row.target_account };\n"
    "    }\n"
    "  }\n"
    "  return { json: { realm_id: row.realm_id, client_id: row.client_id, txn_id: row.txn_id,\n"
    "    new_account: row.target_account, rule_id: row.rule_id, body: p } };\n"
    "});\n", 1760, 200))
upd = wf.add(http("QBO: update purchase",
    "=https://quickbooks.api.intuit.com/v3/company/{{ $json.realm_id }}/purchase?minorversion=73",
    1980, 200, method="POST", cred_type="quickBooksOAuth2Api",
    headers=[("Accept", "application/json")], json_body="={{ JSON.stringify($json.body) }}"))
wf.nodes[-1]["credentials"] = QBO_CRED
log_row = wf.add(code("To rules audit rows",
    "const rows = $('Mutate per rule').all().map(i => i.json);\n"
    "return $input.all().map((i, idx) => ({ json: { applied_at: new Date().toISOString(),\n"
    "  client_id: rows[idx].client_id, txn_id: rows[idx].txn_id, old_account: 'Uncategorized',\n"
    "  new_account: rows[idx].new_account, approved_by: 'rules-engine:' + rows[idx].rule_id } }));\n", 2200, 200))
log = wf.add(sheets_append("Append rules audit", PH["OPS_SHEET"], "Reclass Audit Log", 2420, 200))
patterns = wf.add(code("To pattern rows",
    "return $input.all().map(i => ({ json: { proposed_at: i.json.proposed_at, client_id: i.json.client_id,\n"
    "  pattern: i.json.pattern, occurrences: i.json.occurrences, status: i.json.status } }));\n", 1540, 420))
pat_app = wf.add(sheets_append("Append Proposed Rules", PH["OPS_SHEET"], "Proposed Rules", 1760, 420))
wf.chain(t, rules, profiles, clients, txns, plan, kind)
wf.wire(kind, get, src_out=0)
wf.chain(get, mutate, upd, log_row, log)
wf.wire(kind, patterns, src_out=1)
wf.wire(patterns, pat_app)
wf.write("QMP-10-Virtual-Rules-Engine.workflow.json")

# ------------------------------------------------------------ QMP-11 reminders
wf = WF("QMP-11 Payment Reminders",
        "Daily 8am: reads the Payment Schedule tab and emails the client (cc the payments "
        "coordinator) ahead of each approved federal/state due date. Marks rows reminded.")
t = wf.add(schedule_trigger("Daily 8am", cron="0 8 * * *"))
sched = wf.add(sheets_read("Read Payment Schedule", PH["OPS_SHEET"], "Payment Schedule", 220, 300))
due = wf.add(code("Filter due within 7 days",
    "const now = new Date();\n"
    "return $input.all().filter(i => {\n"
    "  const r = i.json;\n"
    "  if (String(r.approved).toUpperCase() !== 'TRUE') return false;\n"
    "  if (String(r.reminded).toUpperCase() === 'TRUE') return false;\n"
    "  const d = new Date(r.due_date);\n"
    "  if (isNaN(d)) return false;\n"
    "  const days = (d - now) / 86400000;\n"
    "  return days >= -1 && days <= 7;\n"
    "});\n", 440, 300))
send = wf.add({"parameters": {"resource": "message", "operation": "send",
    "sendTo": "={{ $json.client_email }}",
    "subject": "=Estimated tax payment reminder — {{ $json.quarter }} due {{ $json.due_date }}",
    "message": "={{ 'Hi ' + $json.client_name + ',\\n\\nA reminder that your ' + $json.quarter + ' estimated tax payments are due ' + $json.due_date + ':\\n\\n• Federal: $' + $json.federal + '  (pay at https://www.eftps.gov or IRS Direct Pay)\\n• State: $' + $json.state + '  (CA: https://www.ftb.ca.gov/pay)\\n\\nQuestions? Just reply to this email.\\n\\nAstute Advisors' }}",
    "options": {"ccList": PH["PAYMENTS_COORDINATOR_EMAIL"]}},
    "id": "remindsend", "name": "Gmail: send reminder", "type": "n8n-nodes-base.gmail",
    "typeVersion": 2, "position": [660, 300], "credentials": GMAIL_CRED})
mark_row = wf.add(code("To reminded marks",
    "const rows = $('Filter due within 7 days').all().map(i => i.json);\n"
    "return $input.all().map((i, idx) => ({ json: { row_number: rows[idx].row_number, reminded: 'TRUE' } }));\n", 880, 300))
mark = wf.add(sheets_update("Mark reminded", PH["OPS_SHEET"], "Payment Schedule", 1100, 300))
wf.chain(t, sched, due, send, mark_row, mark)
wf.write("QMP-11-Payment-Reminders.workflow.json")

# ---------------------------------------------------------------- QMP-MASTER
def run_node(wf_obj, label, x, y):
    return wf_obj.add({"parameters": {"source": "database",
        "workflowId": {"__rl": True, "mode": "list", "value": "", "cachedResultName": label},
        "mode": "once", "options": {}},
        "id": ("run_" + label)[:30].replace(" ", "_"), "name": "Run: " + label,
        "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2, "position": [x, y]})

wf = WF("QMP-MASTER Quarterly Prep Orchestrator",
        "48h before each 'Quarterly' calendar meeting: builds the client context, runs every "
        "ingestion + analysis sub-workflow, compiles the Meeting Brief, gates on Karen's "
        "approval, then generates the deck, schedules payment reminders, creates the Karbon "
        "work item, and logs the run. Select each sub-workflow in the Run nodes after import.")
t = wf.add(schedule_trigger("Every 6 hours", hours=6))
cal = wf.add({"parameters": {"resource": "event", "operation": "getAll", "returnAll": True,
    "calendar": {"__rl": True, "mode": "list", "value": "primary"},
    "options": {"timeMin": "={{ $now.plus({ hours: 36 }).toISO() }}",
                 "timeMax": "={{ $now.plus({ hours: 60 }).toISO() }}"}},
    "id": "cal", "name": "Get calendar events (36-60h)",
    "type": "n8n-nodes-base.googleCalendar", "typeVersion": 1, "position": [220, 300],
    "credentials": GCAL_CRED})
collect = wf.add(code("Collect quarterly events",
    "const events = $input.all().map(i => i.json).filter(e => String(e.summary ?? '').toLowerCase().includes('quarterly'));\n"
    "return [{ json: { events: events.map(e => ({ summary: e.summary, start: e.start?.dateTime ?? e.start?.date ?? '' })) } }];\n", 440, 300))
profiles = wf.add(sheets_read("Read client profiles", PH["PROFILE_SHEET"], "Sheet1", 660, 300))
runlog = wf.add(sheets_read("Read Run Log", PH["OPS_SHEET"], "Run Log", 880, 300))
match = wf.add(code("Match + dedupe + take one",
    "const events = $('Collect quarterly events').first().json.events ?? [];\n"
    "const profiles = $('Read client profiles').all().map(i => i.json).filter(p => p.client_name);\n"
    "const log = $('Read Run Log').all().map(i => i.json);\n"
    "for (const e of events) {\n"
    "  const p = profiles.find(p => String(e.summary).toLowerCase().includes(String(p.client_name).toLowerCase()));\n"
    "  if (!p) continue;\n"
    "  const meetingDate = String(e.start).slice(0, 10);\n"
    "  const already = log.some(r => r.client_id === p.client_id && r.meeting_date === meetingDate);\n"
    "  if (already) continue;\n"
    "  return [{ json: { ...p, meeting_date: meetingDate, meeting_summary: e.summary, questionnaire: null } }];\n"
    "}\n"
    "return [];\n", 1100, 300))
ask = wf.add(gmail_send("Ask Karen for updates", PH["KAREN_EMAIL"],
    "=Prep input: {{ $json.client_name }}",
    "={{ 'Prepping for ' + $json.client_name + ' on ' + $json.meeting_date + '. Any updates, concerns, or topics to include? Reply to this email (keep the subject) or ignore to skip.' }}",
    1320, 300))
restore0 = wf.add(code("Ctx after ask",
    "return [{ json: $('Match + dedupe + take one').first().json }];\n", 1540, 300))
wf.chain(t, cal, collect, profiles, runlog, match, ask, restore0)

prev = restore0
x = 220
subs = ["QMP-01 Karbon Work Items", "QMP-12 Client Communications Digest",
        "QMP-13 Last-Meeting Recap", "QMP-14 Tax Document Intelligence",
        "QMP-15 Client File Inventory + PMT", "QMP-02 Financial Data (QBO)",
        "QMP-18 Books Health (sub)", "QMP-03 Payroll Parse (manual stubs)"]
for i, label in enumerate(subs):
    n = run_node(wf, label, x + i * 220, 560)
    wf.wire(prev, n)
    prev = n
notes = wf.add(sheets_read("Read Preparer Notes", PH["OPS_SHEET"], "Preparer Notes", 220, 820,
                           filters=[("client_name", "={{ $('Run: QMP-03 Payroll Parse (manual stubs)').first().json.client_name }}")]))
merge_notes = wf.add(code("Merge preparer notes",
    "const ctx = $('Run: QMP-03 Payroll Parse (manual stubs)').first().json;\n"
    "const rows = $input.all().map(i => i.json).filter(r => r.notes);\n"
    "rows.sort((a, b) => String(b.received_at).localeCompare(String(a.received_at)));\n"
    "return [{ json: { ...ctx, preparer_notes: rows[0]?.notes ?? null } }];\n", 440, 820))
wf.wire(prev, notes); wf.wire(notes, merge_notes)
prev = merge_notes
for i, label in enumerate(["QMP-04 Tax Estimate + Entity Comparison", "QMP-05 Client Scorecard",
                            "QMP-17 Tax Strategy Screener", "QMP-19 Meeting Brief Compiler"]):
    n = run_node(wf, label, 660 + i * 220, 820)
    wf.wire(prev, n)
    prev = n

notify = wf.add({"parameters": {"resource": "message", "operation": "send",
    "sendTo": PH["KAREN_EMAIL"],
    "subject": "=Prep ready — {{ $json.client_name }} — approve to release",
    "emailType": "html",
    "message": "={{ '<p>Meeting Brief for <b>' + $json.client_name + '</b> (' + $json.meeting_date + ') is ready.</p><p><a href=\"' + $json.brief_doc_url + '\">Open the brief</a></p><p><a href=\"' + $execution.resumeUrl + '?approved=true\">✅ Approve — generate deck + reminders</a><br><a href=\"' + $execution.resumeUrl + '?approved=false\">✋ Request changes</a></p>' }}",
    "options": {}},
    "id": "notify", "name": "Notify Karen (approve link)", "type": "n8n-nodes-base.gmail",
    "typeVersion": 2, "position": [1540, 820], "credentials": GMAIL_CRED})
gate = wf.add({"parameters": {"resume": "webhook", "options": {}},
    "id": "gate", "name": "APPROVAL GATE (wait)", "type": "n8n-nodes-base.wait",
    "typeVersion": 1.1, "position": [1760, 820], "webhookId": "qmp-prep-approval"})
approved = wf.add({"parameters": {"conditions": {"options": {"caseSensitive": False},
        "conditions": [{"leftValue": "={{ $json.query?.approved ?? $json.approved ?? '' }}",
                         "rightValue": "true", "operator": {"type": "string", "operation": "equals"}}]}},
    "id": "approvedif", "name": "Approved?", "type": "n8n-nodes-base.if",
    "typeVersion": 2, "position": [1980, 820]})
wf.chain(prev, notify, gate, approved)

restore = wf.add(code("Restore ctx (approved)",
    "return [{ json: $('Run: QMP-19 Meeting Brief Compiler').first().json }];\n", 220, 1080))
wf.wire(approved, restore, src_out=0)
deck = run_node(wf, "QMP-20 Presentation Deck", 440, 1080)
wf.wire(restore, deck)
payrows = wf.add(code("To payment schedule rows",
    "const ctx = $json;\n"
    "return (ctx.tax_estimate?.quarterly_payments ?? []).map(q => ({ json: {\n"
    "  client_id: ctx.client_id, client_name: ctx.client_name, client_email: ctx.client_email,\n"
    "  quarter: q.quarter, due_date: q.due_date, federal: q.federal, state: q.state,\n"
    "  approved: 'TRUE', reminded: 'FALSE', notes: 'auto from prep ' + (ctx.meeting_date ?? '') } }));\n", 660, 1080))
pay_app = wf.add(sheets_append("Append Payment Schedule", PH["OPS_SHEET"], "Payment Schedule", 880, 1080))
karbon = wf.add(http("Karbon: meeting work item", "https://api.karbonhq.com/v3/WorkItems",
    1100, 1080, method="POST", cred=KARBON_CRED,
    json_body="={{ JSON.stringify({ Title: 'Quarterly meeting — ' + $('Restore ctx (approved)').first().json.client_name + ' — review brief before ' + $('Restore ctx (approved)').first().json.meeting_date, ClientKey: $('Restore ctx (approved)').first().json.karbon_client_id, DueDate: $('Restore ctx (approved)').first().json.meeting_date }) }}"))
log_row = wf.add(code("To run log row",
    "const ctx = $('Run: QMP-20 Presentation Deck').first().json;\n"
    "return [{ json: { run_date: new Date().toISOString(), client_id: ctx.client_id,\n"
    "  client_name: ctx.client_name, meeting_date: ctx.meeting_date, status: 'approved',\n"
    "  brief_url: ctx.brief_doc_url ?? '', deck_url: ctx.deck_url ?? '',\n"
    "  flags: JSON.stringify(ctx.tax_estimate?.anomalies ?? []) } }];\n", 1320, 1080))
log_app = wf.add(sheets_append("Append Run Log", PH["OPS_SHEET"], "Run Log", 1540, 1080))
done = wf.add(gmail_send("Notify: prep complete", PH["KAREN_EMAIL"],
    "=✓ Prep complete — {{ $('Run: QMP-20 Presentation Deck').first().json.client_name }}",
    "={{ 'Deck: ' + $('Run: QMP-20 Presentation Deck').first().json.deck_url + '\\nBrief: ' + $('Run: QMP-20 Presentation Deck').first().json.brief_doc_url + '\\nPayment reminders scheduled.' }}",
    1760, 1080))
wf.chain(deck, payrows, pay_app, karbon, log_row, log_app, done)

changes_row = wf.add(code("To run log row (changes)",
    "const ctx = $('Run: QMP-19 Meeting Brief Compiler').first().json;\n"
    "return [{ json: { run_date: new Date().toISOString(), client_id: ctx.client_id,\n"
    "  client_name: ctx.client_name, meeting_date: ctx.meeting_date, status: 'changes_requested',\n"
    "  brief_url: ctx.brief_doc_url ?? '', deck_url: '', flags: '' } }];\n", 220, 1340))
wf.wire(approved, changes_row, src_out=1)
changes_app = wf.add(sheets_append("Append Run Log (changes)", PH["OPS_SHEET"], "Run Log", 440, 1340))
changes_mail = wf.add(gmail_send("Notify: changes requested", PH["KAREN_EMAIL"],
    "=Changes requested — {{ $('Run: QMP-19 Meeting Brief Compiler').first().json.client_name }}",
    "={{ 'Noted. Edit the brief doc directly, then re-run the prep from n8n (delete the Run Log row for this meeting first so the orchestrator picks it up again): ' + $('Run: QMP-19 Meeting Brief Compiler').first().json.brief_doc_url }}",
    660, 1340))
wf.chain(changes_row, changes_app, changes_mail)
wf.write("QMP-MASTER-Orchestrator.workflow.json")

print("Ops workflows + master generated.")
