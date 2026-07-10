#!/usr/bin/env python3
"""Generates the ingestion + AI sub-workflows (called by the master orchestrator).

Each sub-workflow starts with an Execute Workflow Trigger named "Input" that
receives the client context (profile row + data accumulated so far) and returns
the context extended with its own output key.

Run:  python3 build_sub_workflows.py
"""
from qmp_lib import (WF, PH, P, exec_trigger, code, http, sheets_read,
                     qbo_get, claude_trio, payload_js,
                     GOOGLE_DRIVE_CRED, GOOGLE_DOCS_CRED, KARBON_CRED)
import json

# --------------------------------------------------------------- QMP-01 Karbon
wf = WF("QMP-01 Karbon Work Items",
        "Pulls the client's Karbon work items: open items + items completed since the "
        "last meeting (the 'what we've done for you' story). Returns ctx + karbon_items.")
t = wf.add(exec_trigger())
open_items = wf.add(http(
    "Karbon: open work items", "https://api.karbonhq.com/v3/WorkItems", 220, 300,
    cred=KARBON_CRED,
    qs=[("$filter", "=ClientKey eq '{{ $('Input').first().json.karbon_client_id }}' and WorkStatus ne 'Completed'")]))
done_items = wf.add(http(
    "Karbon: completed since last meeting", "https://api.karbonhq.com/v3/WorkItems", 440, 300,
    cred=KARBON_CRED,
    qs=[("$filter", "=ClientKey eq '{{ $('Input').first().json.karbon_client_id }}' and WorkStatus eq 'Completed' and CompletedDate ge {{ $('Input').first().json.last_meeting_date }}")]))
fmt = wf.add(code("Format work items",
    "const ctx = $('Input').first().json;\n"
    "const compact = (r) => ({ title: r.Title, status: r.WorkStatus, due: r.DueDate ?? null,\n"
    "  assignee: r.AssigneeEmailAddress ?? r.AssigneeName ?? null, type: r.WorkType ?? null });\n"
    "const open = ($('Karbon: open work items').first().json.value ?? []).map(compact);\n"
    "const completed = ($('Karbon: completed since last meeting').first().json.value ?? []).map(compact);\n"
    "return [{ json: { ...ctx, karbon_items: { open, completed } } }];\n", 660, 300))
wf.chain(t, open_items, done_items, fmt)
wf.write("QMP-01-Karbon-Work-Items.workflow.json")

# ----------------------------------------------------------- QMP-02 Financials
wf = WF("QMP-02 Financial Data (QBO)",
        "Pulls P&L (current YTD, last 12mo, prior 12mo) and Balance Sheet from the "
        "client's QBO. Returns ctx + financials.")
t = wf.add(exec_trigger())
pl_ytd = wf.add(qbo_get("QBO: P&L current YTD", "/reports/ProfitAndLoss", 220, 300, qs=[
    ("start_date", "={{ $now.startOf('year').toFormat('yyyy-MM-dd') }}"),
    ("end_date", "={{ $now.toFormat('yyyy-MM-dd') }}")]))
pl_12 = wf.add(qbo_get("QBO: P&L last 12mo", "/reports/ProfitAndLoss", 440, 300, qs=[
    ("start_date", "={{ $now.minus({ months: 12 }).toFormat('yyyy-MM-dd') }}"),
    ("end_date", "={{ $now.toFormat('yyyy-MM-dd') }}")]))
pl_prior = wf.add(qbo_get("QBO: P&L prior 12mo", "/reports/ProfitAndLoss", 660, 300, qs=[
    ("start_date", "={{ $now.minus({ months: 24 }).toFormat('yyyy-MM-dd') }}"),
    ("end_date", "={{ $now.minus({ months: 12 }).toFormat('yyyy-MM-dd') }}")]))
bs = wf.add(qbo_get("QBO: Balance Sheet", "/reports/BalanceSheet", 880, 300))
fmt = wf.add(code("Combine financials",
    "const ctx = $('Input').first().json;\n"
    "return [{ json: { ...ctx, financials: {\n"
    "  pnl_ytd: $('QBO: P&L current YTD').first().json,\n"
    "  pnl_last_12mo: $('QBO: P&L last 12mo').first().json,\n"
    "  pnl_prior_12mo: $('QBO: P&L prior 12mo').first().json,\n"
    "  balance_sheet: $('QBO: Balance Sheet').first().json,\n"
    "} } }];\n", 1100, 300))
wf.chain(t, pl_ytd, pl_12, pl_prior, bs, fmt)
wf.write("QMP-02-Financial-Data.workflow.json")

# -------------------------------------------------------- QMP-03 Payroll parse
wf = WF("QMP-03 Payroll Parse (manual stubs)",
        "Reads the newest pay stub PDFs the team manually uploaded to the client's Drive "
        "folder and has Claude extract YTD withholdings. No payroll system connections — "
        "per DATA-GOVERNANCE. Returns ctx + payroll.")
t = wf.add(exec_trigger())
ids = wf.add(code("Extract folder id",
    "const ctx = $('Input').first().json;\n"
    "const m = String(ctx.google_drive_folder ?? '').match(/[-\\w]{25,}/);\n"
    "return [{ json: { ...ctx, drive_folder_id: m ? m[0] : '' } }];\n", 220, 300))
ls = wf.add(http("Drive: list pay stub PDFs", "https://www.googleapis.com/drive/v3/files", 440, 300,
    cred_type="googleDriveOAuth2Api",
    qs=[("q", "='{{ $json.drive_folder_id }}' in parents and mimeType='application/pdf' and (name contains 'stub' or name contains 'Stub' or name contains 'payroll' or name contains 'Payroll')"),
        ("orderBy", "modifiedTime desc"), ("pageSize", "2"), ("fields", "files(id,name,modifiedTime)")]))
split = wf.add(code("Split file list",
    "const files = ($json.files ?? []).slice(0, 2);\n"
    "if (!files.length) { return [{ json: { no_stubs: true } }]; }\n"
    "return files.map(f => ({ json: f }));\n", 660, 300))
dl = wf.add(http("Drive: download stub", "=https://www.googleapis.com/drive/v3/files/{{ $json.id }}?alt=media",
                 880, 300, cred_type="googleDriveOAuth2Api", response_file=True))
build = wf.add(code("Build request: payroll",
    "const ctx = $('Input').first().json;\n"
    "const items = $input.all();\n"
    "const docs = [];\n"
    "for (const it of items) {\n"
    "  const b64 = it.binary?.data?.data;\n"
    "  if (b64) docs.push({ type: 'document', source: { type: 'base64', media_type: 'application/pdf', data: b64 } });\n"
    "}\n"
    "if (!docs.length) { return [{ json: { ...ctx, payroll: { employees: [], notes: ['No pay stubs found in Drive folder'] } } }]; }\n"
    "const payload = {\n"
    "  model: 'claude-opus-4-8', max_tokens: 8000,\n"
    "  system: " + json.dumps(P["payroll"]["system"]) + ",\n"
    "  messages: [{ role: 'user', content: [...docs, { type: 'text', text: 'Extract the payroll data from these pay stubs for client ' + ctx.client_name + '.' }] }],\n"
    "  output_config: { effort: 'high', format: { type: 'json_schema', schema: " + json.dumps(P["payroll"]["schema"]) + " } }\n"
    "};\n"
    "return [{ json: { payload } }];\n", 1100, 300))
claude = wf.add(http("Claude: payroll", "https://api.anthropic.com/v1/messages", 1320, 300,
    method="POST", cred_type="anthropicApi",
    headers=[("anthropic-version", "2023-06-01")], json_body="={{ JSON.stringify($json.payload) }}"))
parse = wf.add(code("Parse: payroll",
    "const ctx = $('Input').first().json;\n"
    "if ($json.payroll) { return [{ json: $json }]; }\n"  # pass-through when no stubs
    "const text = $json.content?.[0]?.text ?? '{}';\n"
    "let out; try { out = JSON.parse(text); } catch (e) { out = { parse_error: true, raw: text }; }\n"
    "return [{ json: { ...ctx, payroll: out } }];\n", 1540, 300))
wf.chain(t, ids, ls, split, dl, build, claude, parse)
wf.write("QMP-03-Payroll-Parse.workflow.json")

# --------------------------------------------------------- QMP-04 Tax estimate
wf = WF("QMP-04 Tax Estimate + Entity Comparison",
        "Computes draft quarterly estimated payments (federal + state + PTE) and the "
        "with/without C-corp comparison from ctx.financials + ctx.payroll + ctx.tax_position. "
        "Returns ctx + tax_estimate. Draft for preparer review — never final.")
t = wf.add(exec_trigger())
user_expr = ("'Client: ' + ctx.client_name + '\\nEntity type: ' + ctx.entity_type + '   State: ' + ctx.state_primary +\n"
             "'\\nHas C-Corp: ' + ctx.has_c_corp + '   PTE election: ' + ctx.has_pte_election +\n"
             "'\\n\\n--- PROJECTED FINANCIALS (from QBO) ---\\n' + JSON.stringify(ctx.financials ?? {}) +\n"
             "'\\n\\n--- OWNER W-2 / WITHHOLDINGS (from pay stubs) ---\\n' + JSON.stringify(ctx.payroll ?? {}) +\n"
             "'\\n\\n--- PRIOR-YEAR TAX POSITION ---\\n' + JSON.stringify(ctx.tax_position ?? {}) +\n"
             "'\\n\\nRates: Federal individual per brackets; CA PTE 9.3%; C-corp 21% federal / 8.84% CA. ' +\n"
             "'CA quarterly schedule 30/40/0/30; Federal 25/25/25/25.'")
claude_trio(wf, "tax estimate",
            payload_js(P["estimate"]["system"], P["estimate"]["schema"], user_expr,
                       max_tokens=16000, thinking=True),
            220, 300, t, "tax_estimate")
wf.write("QMP-04-Tax-Estimate.workflow.json")

# ------------------------------------------------------------ QMP-05 Scorecard
wf = WF("QMP-05 Client Scorecard",
        "Builds the 4-metric scorecard + tax-story narrative from ctx.financials and "
        "ctx.payroll. Returns ctx + scorecard.")
t = wf.add(exec_trigger())
user_expr = ("'Client: ' + ctx.client_name +\n"
             "'\\n--- P&L (current 12mo + prior 12mo) ---\\n' + JSON.stringify({ last12: ctx.financials?.pnl_last_12mo, prior12: ctx.financials?.pnl_prior_12mo }) +\n"
             "'\\n--- BALANCE SHEET ---\\n' + JSON.stringify(ctx.financials?.balance_sheet ?? {}) +\n"
             "'\\n--- PAYROLL ---\\n' + JSON.stringify(ctx.payroll ?? {})")
claude_trio(wf, "scorecard",
            payload_js(P["scorecard"]["system"], P["scorecard"]["schema"], user_expr),
            220, 300, t, "scorecard")
wf.write("QMP-05-Client-Scorecard.workflow.json")

# --------------------------------------------------------------- QMP-12 Digest
wf = WF("QMP-12 Client Communications Digest",
        "Pulls client emails since the last meeting from Karen's Astute Gmail and digests "
        "them (commitments, questions, changes, sentiment). Returns ctx + email_digest.")
t = wf.add(exec_trigger())
mail = wf.add({"parameters": {"operation": "getAll", "returnAll": False, "limit": 50, "simple": True,
    "filters": {"q": "={{ '(from:' + $('Input').first().json.gmail_query_alias + ' OR to:' + $('Input').first().json.gmail_query_alias + ') after:' + ($('Input').first().json.last_meeting_date || '2020/01/01').replaceAll('-', '/') }}"},
    "options": {}},
    "id": "gmail_pull", "name": "Gmail: client threads since last meeting",
    "type": "n8n-nodes-base.gmail", "typeVersion": 2, "position": [220, 300],
    "credentials": {"gmailOAuth2": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Gmail"}}})
compact = wf.add(code("Compact messages",
    "const ctx = $('Input').first().json;\n"
    "const msgs = $input.all().map(i => i.json).map(m => ({\n"
    "  from: m.from?.value?.[0]?.address ?? m.From ?? '', subject: m.subject ?? m.Subject ?? '',\n"
    "  date: m.date ?? m.internalDate ?? '', snippet: (m.textPlain ?? m.snippet ?? '').slice(0, 1500)\n"
    "}));\n"
    "return [{ json: { ...ctx, communications: msgs } }];\n", 440, 300))
user_expr = ("'Client: ' + ctx.client_name + '\\nLast meeting date: ' + ctx.last_meeting_date +\n"
             "'\\n\\nCommunications since the last meeting:\\n' + JSON.stringify($json.communications ?? [])")
claude_trio(wf, "email digest",
            payload_js(P["digest"]["system"], P["digest"]["schema"], user_expr),
            660, 300, compact, "email_digest")
wf.wire(t, mail); wf.wire(mail, compact)
wf.write("QMP-12-Comms-Digest.workflow.json")

# ---------------------------------------------------------------- QMP-13 Recap
wf = WF("QMP-13 Last-Meeting Recap",
        "Reads the prior meeting's stored summary/transcript from the Meeting History tab "
        "(written by QMP-08 post-meeting) and cross-references promises against "
        "ctx.karbon_items -> Done/Pending/Blocked. Returns ctx + recap.")
t = wf.add(exec_trigger())
hist = wf.add(sheets_read("Read Meeting History", PH["OPS_SHEET"], "Meeting History", 220, 300,
                          filters=[("client_id", "={{ $('Input').first().json.client_id }}")]))
latest = wf.add(code("Pick latest meeting record",
    "const ctx = $('Input').first().json;\n"
    "const rows = $input.all().map(i => i.json).filter(r => r.client_id);\n"
    "rows.sort((a, b) => String(b.meeting_date).localeCompare(String(a.meeting_date)));\n"
    "const last = rows[0] ?? null;\n"
    "return [{ json: { ...ctx, last_meeting_record: last } }];\n", 440, 300))
user_expr = ("'Client: ' + ctx.client_name +\n"
             "'\\n\\n--- PRIOR MEETING TRANSCRIPT/SUMMARY ---\\n' + JSON.stringify($json.last_meeting_record ?? 'No prior meeting on record') +\n"
             "'\\n\\n--- CURRENT KARBON WORK ITEMS ---\\n' + JSON.stringify(ctx.karbon_items ?? {})")
claude_trio(wf, "recap",
            payload_js(P["recap"]["system"], P["recap"]["schema"], user_expr),
            660, 300, latest, "recap")
wf.wire(t, hist); wf.wire(hist, latest)
wf.write("QMP-13-Last-Meeting-Recap.workflow.json")

# ------------------------------------------------------------- QMP-14 Tax docs
wf = WF("QMP-14 Tax Document Intelligence",
        "Downloads the newest tax return / prior plan PDFs from the client's tax folder "
        "and extracts the Tax Position (carryforwards, elections, safe harbor). Returns "
        "ctx + tax_position.")
t = wf.add(exec_trigger())
ids = wf.add(code("Extract tax folder id",
    "const ctx = $('Input').first().json;\n"
    "const m = String(ctx.drive_tax_folder ?? '').match(/[-\\w]{25,}/);\n"
    "return [{ json: { ...ctx, tax_folder_id: m ? m[0] : '' } }];\n", 220, 300))
ls = wf.add(http("Drive: list tax PDFs", "https://www.googleapis.com/drive/v3/files", 440, 300,
    cred_type="googleDriveOAuth2Api",
    qs=[("q", "='{{ $json.tax_folder_id }}' in parents and mimeType='application/pdf'"),
        ("orderBy", "modifiedTime desc"), ("pageSize", "3"), ("fields", "files(id,name,modifiedTime)")]))
split = wf.add(code("Split tax file list",
    "const files = ($json.files ?? []).slice(0, 3);\n"
    "if (!files.length) { return [{ json: { no_docs: true } }]; }\n"
    "return files.map(f => ({ json: f }));\n", 660, 300))
dl = wf.add(http("Drive: download tax doc", "=https://www.googleapis.com/drive/v3/files/{{ $json.id }}?alt=media",
                 880, 300, cred_type="googleDriveOAuth2Api", response_file=True))
build = wf.add(code("Build request: tax position",
    "const ctx = $('Input').first().json;\n"
    "const items = $input.all();\n"
    "const docs = [];\n"
    "for (const it of items) {\n"
    "  const b64 = it.binary?.data?.data;\n"
    "  if (b64) docs.push({ type: 'document', source: { type: 'base64', media_type: 'application/pdf', data: b64 } });\n"
    "}\n"
    "if (!docs.length) { return [{ json: { ...ctx, tax_position: { notes: ['No tax documents found'], tax_year: null, agi: null, taxable_income: null, marginal_rate: null, effective_rate: null, carryforwards: [], elections: [], estimates_paid: null, safe_harbor_target: null } } }]; }\n"
    "const payload = {\n"
    "  model: 'claude-opus-4-8', max_tokens: 8000,\n"
    "  system: " + json.dumps(P["taxpos"]["system"]) + ",\n"
    "  messages: [{ role: 'user', content: [...docs, { type: 'text', text: 'Extract the tax position for client ' + ctx.client_name + '.' }] }],\n"
    "  output_config: { effort: 'high', format: { type: 'json_schema', schema: " + json.dumps(P["taxpos"]["schema"]) + " } }\n"
    "};\n"
    "return [{ json: { payload } }];\n", 1100, 300))
claude = wf.add(http("Claude: tax position", "https://api.anthropic.com/v1/messages", 1320, 300,
    method="POST", cred_type="anthropicApi",
    headers=[("anthropic-version", "2023-06-01")], json_body="={{ JSON.stringify($json.payload) }}"))
parse = wf.add(code("Parse: tax position",
    "const ctx = $('Input').first().json;\n"
    "if ($json.tax_position) { return [{ json: $json }]; }\n"
    "const text = $json.content?.[0]?.text ?? '{}';\n"
    "let out; try { out = JSON.parse(text); } catch (e) { out = { parse_error: true, raw: text }; }\n"
    "return [{ json: { ...ctx, tax_position: out } }];\n", 1540, 300))
wf.chain(t, ids, ls, split, dl, build, claude, parse)
wf.write("QMP-14-Tax-Document-Intelligence.workflow.json")

# ------------------------------------------------------------ QMP-15 Inventory
wf = WF("QMP-15 Client File Inventory + PMT",
        "Lists the full client Drive folder, reads the PMT schedule when present, and "
        "produces a relevance triage + payment schedule status. Returns ctx + file_inventory.")
t = wf.add(exec_trigger())
ids = wf.add(code("Extract folder + PMT ids",
    "const ctx = $('Input').first().json;\n"
    "const fid = String(ctx.google_drive_folder ?? '').match(/[-\\w]{25,}/);\n"
    "const pid = String(ctx.pmt_file_link ?? '').match(/[-\\w]{25,}/);\n"
    "return [{ json: { ...ctx, drive_folder_id: fid ? fid[0] : '', pmt_id: pid ? pid[0] : '' } }];\n", 220, 300))
ls = wf.add(http("Drive: list client files", "https://www.googleapis.com/drive/v3/files", 440, 300,
    cred_type="googleDriveOAuth2Api",
    qs=[("q", "='{{ $json.drive_folder_id }}' in parents and trashed=false"),
        ("orderBy", "modifiedTime desc"), ("pageSize", "100"),
        ("fields", "files(id,name,mimeType,modifiedTime)")]))
haspmt = wf.add({"parameters": {"conditions": {"options": {"caseSensitive": True},
        "conditions": [{"leftValue": "={{ $('Extract folder + PMT ids').first().json.pmt_id }}",
                         "rightValue": "", "operator": {"type": "string", "operation": "notEquals"}}]}},
    "id": "haspmt", "name": "Has PMT file?", "type": "n8n-nodes-base.if",
    "typeVersion": 2, "position": [660, 300]})
pmt = wf.add(http("Export PMT (csv)",
    "=https://www.googleapis.com/drive/v3/files/{{ $('Extract folder + PMT ids').first().json.pmt_id }}/export?mimeType=text/csv",
    880, 200, cred_type="googleDriveOAuth2Api"))
build_js = (
    "const ctx = $('Input').first().json;\n"
    "const files = ($('Drive: list client files').first().json.files ?? []).map(f => ({ name: f.name, type: f.mimeType, modified: f.modifiedTime }));\n"
    "let pmt = 'No PMT file on record';\n"
    "try { const p = $('Export PMT (csv)').first().json; pmt = typeof p === 'string' ? p : (p.data ?? JSON.stringify(p)); } catch (e) {}\n"
    "const userContent = 'Client: ' + ctx.client_name + '\\n\\n--- FILE LISTING ---\\n' + JSON.stringify(files) + '\\n\\n--- PMT SCHEDULE (csv) ---\\n' + String(pmt).slice(0, 20000);\n"
    "const payload = {\n"
    "  model: 'claude-opus-4-8', max_tokens: 8000,\n"
    "  system: " + json.dumps(P["inventory"]["system"]) + ",\n"
    "  messages: [{ role: 'user', content: userContent }],\n"
    "  output_config: { effort: 'high', format: { type: 'json_schema', schema: " + json.dumps(P["inventory"]["schema"]) + " } }\n"
    "};\n"
    "return [{ json: { payload } }];\n")
build = wf.add(code("Build request: inventory", build_js, 1100, 300))
claude = wf.add(http("Claude: inventory", "https://api.anthropic.com/v1/messages", 1320, 300,
    method="POST", cred_type="anthropicApi",
    headers=[("anthropic-version", "2023-06-01")], json_body="={{ JSON.stringify($json.payload) }}"))
parse = wf.add(code("Parse: inventory",
    "const ctx = $('Input').first().json;\n"
    "const text = $json.content?.[0]?.text ?? '{}';\n"
    "let out; try { out = JSON.parse(text); } catch (e) { out = { parse_error: true, raw: text }; }\n"
    "return [{ json: { ...ctx, file_inventory: out } }];\n", 1540, 300))
wf.chain(t, ids, ls, haspmt)
wf.wire(haspmt, pmt, src_out=0)     # true -> export PMT
wf.wire(pmt, build)
wf.wire(haspmt, build, src_out=1)   # false -> straight to build
wf.chain(build, claude, parse)
wf.write("QMP-15-File-Inventory.workflow.json")

# ------------------------------------------------------------- QMP-17 Screener
wf = WF("QMP-17 Tax Strategy Screener",
        "Screens every Firm-Approved strategy in the library against the client's fresh "
        "data; filters implemented/rejected; ranks by estimated savings. Returns ctx + strategies.")
t = wf.add(exec_trigger())
lib = wf.add(sheets_read("Read Strategy Library", PH["LIBRARY_SHEET"], "Strategy Library", 220, 300,
                         filters=[("review_status", "Firm-Approved")]))
status = wf.add(sheets_read("Read Client Strategy Status", PH["STATUS_SHEET"], "Client Strategy Status",
                            440, 300, filters=[("client_id", "={{ $('Input').first().json.client_id }}")]))
merge = wf.add(code("Assemble screener input",
    "const ctx = $('Input').first().json;\n"
    "const library = $('Read Strategy Library').all().map(i => i.json);\n"
    "const clientStatus = $('Read Client Strategy Status').all().map(i => i.json).filter(r => r.client_id);\n"
    "return [{ json: { ...ctx, _library: library, _client_status: clientStatus } }];\n", 660, 300))
user_expr = ("'Client: ' + ctx.client_name +\n"
             "'\\n\\n--- STRATEGY LIBRARY (Firm-Approved rows) ---\\n' + JSON.stringify($json._library ?? []) +\n"
             "'\\n\\n--- CLIENT DATA (financials + tax position + profile + questionnaire) ---\\n' +\n"
             "JSON.stringify({ profile: { entity_type: ctx.entity_type, state: ctx.state_primary, has_c_corp: ctx.has_c_corp, has_pte_election: ctx.has_pte_election },\n"
             "  financials: ctx.financials ?? null, tax_position: ctx.tax_position ?? null,\n"
             "  payroll: ctx.payroll ?? null, questionnaire: ctx.questionnaire ?? null, email_digest: ctx.email_digest ?? null }) +\n"
             "'\\n\\n--- ALREADY IMPLEMENTED / REJECTED FOR THIS CLIENT ---\\n' + JSON.stringify($json._client_status ?? [])")
claude_trio(wf, "strategy screener",
            payload_js(P["screener"]["system"], P["screener"]["schema"], user_expr,
                       max_tokens=16000, thinking=True),
            880, 300, merge, "strategies")
wf.wire(t, lib); wf.wire(lib, status); wf.wire(status, merge)
wf.write("QMP-17-Strategy-Screener.workflow.json")

# ----------------------------------------------------------------- QMP-19 Brief
wf = WF("QMP-19 Meeting Brief Compiler",
        "Compiles all upstream outputs into the 9-section Meeting Brief, renders it, and "
        "creates the Google Doc in the Astute briefs folder. Returns ctx + brief + brief_doc_url.")
t = wf.add(exec_trigger())
user_expr = ("'Client: ' + ctx.client_name + '   Meeting: ' + (ctx.meeting_date ?? '') +\n"
             "'\\n\\nEMAIL DIGEST: ' + JSON.stringify(ctx.email_digest ?? null) +\n"
             "'\\nLAST-MEETING RECAP: ' + JSON.stringify(ctx.recap ?? null) +\n"
             "'\\nBOOKS HEALTH: ' + JSON.stringify(ctx.books_health ?? null) +\n"
             "'\\nTAX ESTIMATE: ' + JSON.stringify(ctx.tax_estimate ?? null) +\n"
             "'\\nSTRATEGY SCREENER: ' + JSON.stringify(ctx.strategies ?? null) +\n"
             "'\\nSCORECARD: ' + JSON.stringify(ctx.scorecard ?? null) +\n"
             "'\\nKARBON OPEN ITEMS: ' + JSON.stringify(ctx.karbon_items ?? null) +\n"
             "'\\nFILE INVENTORY / PMT: ' + JSON.stringify(ctx.file_inventory ?? null) +\n"
             "'\\nCLIENT QUESTIONNAIRE: ' + JSON.stringify(ctx.questionnaire ?? null) +\n"
             "'\\nPREPARER NOTES (Karen): ' + JSON.stringify(ctx.preparer_notes ?? null)")
parse = claude_trio(wf, "meeting brief",
                    payload_js(P["brief"]["system"], P["brief"]["schema"], user_expr,
                               max_tokens=16000, thinking=True),
                    220, 300, t, "brief")
render = wf.add(code("Render brief text",
    "const ctx = $json;\n"
    "const b = ctx.brief ?? {};\n"
    "const money = (n) => n == null ? 'TBD' : ('$' + Math.round(n).toLocaleString('en-US'));\n"
    "const lines = [];\n"
    "lines.push('MEETING BRIEF — ' + ctx.client_name + ' — ' + (ctx.meeting_date ?? ''));\n"
    "lines.push('Internal preparation document. Draft for professional review — not client-facing.');\n"
    "lines.push('');\n"
    "lines.push('1. EXECUTIVE SUMMARY');\n"
    "(b.executive_summary ?? []).forEach(s => lines.push('  • ' + s));\n"
    "lines.push(''); lines.push('2. SINCE LAST MEETING'); lines.push(b.since_last_meeting ?? '');\n"
    "lines.push(''); lines.push('3. FOLLOW-UP ITEMS');\n"
    "(b.follow_up_items ?? []).forEach(f => lines.push('  • [' + f.owner + '] ' + f.item));\n"
    "lines.push(''); lines.push('4. FINANCIAL REVIEW'); lines.push(b.financial_review ?? '');\n"
    "lines.push(''); lines.push('5. BOOKS HEALTH'); lines.push(b.books_health ?? '');\n"
    "lines.push(''); lines.push('6. TAX POSITION'); lines.push(b.tax_position ?? '');\n"
    "lines.push(''); lines.push('7. STRATEGY OPPORTUNITIES (to evaluate — not recommendations)');\n"
    "(b.strategy_opportunities ?? []).forEach(s => lines.push('  • ' + s.strategy + ' — est. ' + money(s.estimated_savings) + (s.needs_memo ? '  [needs Blue J memo + sign-off]' : '')));\n"
    "lines.push(''); lines.push('8. KEY TALKING POINTS');\n"
    "(b.key_talking_points ?? []).forEach((p, i) => lines.push('  ' + (i + 1) + '. ' + p));\n"
    "lines.push(''); lines.push('9. QUESTIONS FOR THE CLIENT');\n"
    "(b.questions_for_client ?? []).forEach(q => lines.push('  • ' + q));\n"
    "return [{ json: { ...ctx, brief_text: lines.join('\\n') } }];\n", 880, 300))
create = wf.add({"parameters": {"resource": "document", "operation": "create",
        "folderId": PH["BRIEF_FOLDER"],
        "title": "=Meeting Brief — {{ $json.client_name }} — {{ $now.toFormat('yyyy-MM-dd') }}"},
    "id": "createdoc", "name": "Create Brief Doc", "type": "n8n-nodes-base.googleDocs",
    "typeVersion": 2, "position": [1100, 300], "credentials": GOOGLE_DOCS_CRED})
insert = wf.add({"parameters": {"resource": "document", "operation": "update",
        "documentURL": "={{ $json.id }}",
        "actionsUi": {"actionFields": [{"action": "insert", "text": "={{ $('Render brief text').first().json.brief_text }}"}]}},
    "id": "insertdoc", "name": "Insert Brief Text", "type": "n8n-nodes-base.googleDocs",
    "typeVersion": 2, "position": [1320, 300], "credentials": GOOGLE_DOCS_CRED})
out = wf.add(code("Return brief + doc url",
    "const prev = $('Render brief text').first().json;\n"
    "const docId = $('Create Brief Doc').first().json.id ?? $('Create Brief Doc').first().json.documentId;\n"
    "return [{ json: { ...prev, brief_doc_id: docId, brief_doc_url: 'https://docs.google.com/document/d/' + docId + '/edit' } }];\n", 1540, 300))
wf.chain(parse, render, create, insert, out)
wf.write("QMP-19-Meeting-Brief.workflow.json")

# ------------------------------------------------------------------ QMP-20 Deck
wf = WF("QMP-20 Presentation Deck",
        "Copies the Astute deck template and fills placeholders from the approved brief "
        "via the Slides API. Returns ctx + deck_url. Runs only after the approval gate.")
t = wf.add(exec_trigger())
copy = wf.add(http("Drive: copy deck template",
    "https://www.googleapis.com/drive/v3/files/" + PH["DECK_TEMPLATE"] + "/copy",
    220, 300, method="POST", cred_type="googleDriveOAuth2Api",
    json_body="={{ JSON.stringify({ name: 'Quarterly Deck — ' + $json.client_name + ' — ' + $now.toFormat('yyyy-MM-dd') }) }}"))
reqs = wf.add(code("Build replaceAllText requests",
    "const ctx = $('Input').first().json;\n"
    "const b = ctx.brief ?? {}; const sc = ctx.scorecard ?? {}; const te = ctx.tax_estimate ?? {};\n"
    "const money = (n) => n == null ? 'TBD' : ('$' + Math.round(n).toLocaleString('en-US'));\n"
    "const pct = (n) => n == null ? 'TBD' : ((n * 100).toFixed(1) + '%');\n"
    "const q1 = (te.quarterly_payments ?? [])[0] ?? {};\n"
    "const strategies = (b.strategy_opportunities ?? []).slice(0, 3).map(s => s.strategy + ' (' + money(s.estimated_savings) + ')').join('\\n') || 'Under review';\n"
    "const repl = {\n"
    "  CLIENT_NAME: ctx.client_name ?? '', MEETING_DATE: ctx.meeting_date ?? '',\n"
    "  EXEC_SUMMARY: (b.executive_summary ?? []).join('\\n'),\n"
    "  REVENUE: money(sc.revenue?.current), REVENUE_CHANGE: pct((sc.revenue?.pct_change ?? 0) / 100),\n"
    "  TAKE_HOME: money(sc.owner_take_home?.current), NET_MARGIN: pct(sc.net_margin?.current),\n"
    "  TAX_SAVINGS: money(te.entity_comparison?.savings),\n"
    "  Q_FED: money(q1.federal), Q_STATE: money(q1.state), Q_DUE: q1.due_date ?? 'TBD',\n"
    "  STRATEGIES: strategies,\n"
    "  NEXT_90: (b.key_talking_points ?? []).slice(0, 3).join('\\n'),\n"
    "};\n"
    "const requests = Object.entries(repl).map(([k, v]) => ({ replaceAllText: {\n"
    "  containsText: { text: '{{' + k + '}}', matchCase: true }, replaceText: String(v) } }));\n"
    "return [{ json: { presentationId: $json.id, requests } }];\n", 440, 300))
fill = wf.add(http("Slides: fill placeholders",
    "=https://slides.googleapis.com/v1/presentations/{{ $json.presentationId }}:batchUpdate",
    660, 300, method="POST", cred_type="googleSlidesOAuth2Api",
    json_body="={{ JSON.stringify({ requests: $json.requests }) }}"))
fill_node = wf.nodes[-1]
fill_node["credentials"] = {"googleSlidesOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google Slides"}}
out = wf.add(code("Return deck url",
    "const ctx = $('Input').first().json;\n"
    "const pid = $('Build replaceAllText requests').first().json.presentationId;\n"
    "return [{ json: { ...ctx, deck_id: pid, deck_url: 'https://docs.google.com/presentation/d/' + pid + '/edit' } }];\n", 880, 300))
wf.chain(t, copy, reqs, fill, out)
wf.write("QMP-20-Presentation-Deck.workflow.json")

print("Sub-workflows generated.")
