#!/usr/bin/env python3
"""Shared library for generating the Astute QMP n8n workflows.

Every workflow is emitted as an importable n8n JSON. Conventions:
- All Google/Gmail/QBO/Anthropic nodes carry Karen's Astute credential
  placeholders (per ../DATA-GOVERNANCE.md — Astute accounts only).
- Sub-workflows start with an Execute Workflow Trigger named "Input"; the
  master passes a context object (client profile row + accumulated data).
  Nodes reference it via $('Input').first().json.<field>.
- AI steps follow the proven pattern from the Books Health worked example:
  Code "Build request" -> HTTP "Claude" -> Code "Parse".
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- credentials
GOOGLE_SHEETS_CRED = {"googleSheetsOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google Sheets"}}
GOOGLE_DOCS_CRED = {"googleDocsOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google Docs"}}
GOOGLE_DRIVE_CRED = {"googleDriveOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google Drive"}}
GCAL_CRED = {"googleCalendarOAuth2Api": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Google Calendar"}}
GMAIL_CRED = {"gmailOAuth2": {"id": "REPLACE_ASTUTE_GOOGLE", "name": "Karen Astute Advisors Gmail"}}
QBO_CRED = {"quickBooksOAuth2Api": {"id": "REPLACE_ASTUTE_QBO", "name": "Karen Astute Advisors QuickBooks"}}
ANTHROPIC_CRED = {"anthropicApi": {"id": "REPLACE_ASTUTE_ANTHROPIC", "name": "Karen Astute Advisors Anthropic"}}
KARBON_CRED = {"httpHeaderAuth": {"id": "REPLACE_ASTUTE_KARBON", "name": "Karen Astute Advisors Karbon (header auth)"}}
FATHOM_CRED = {"httpHeaderAuth": {"id": "REPLACE_ASTUTE_FATHOM", "name": "Karen Astute Advisors Fathom (header auth)"}}

# Shared placeholder IDs the firm pastes once (documented in DEPLOYMENT.md)
PH = {
    "PROFILE_SHEET": "PASTE_CLIENT_PROFILE_MATRIX_SHEET_ID",
    "LIBRARY_SHEET": "PASTE_TAX_STRATEGY_LIBRARY_SHEET_ID",
    "STATUS_SHEET": "PASTE_CLIENT_STRATEGY_STATUS_SHEET_ID",
    "OPS_SHEET": "PASTE_QMP_OPERATIONS_SHEET_ID",
    "KAREN_EMAIL": "PASTE_KAREN_EMAIL",
    "PAYMENTS_COORDINATOR_EMAIL": "PASTE_CHRISTINA_EMAIL",
    "BRIEF_FOLDER": "PASTE_ASTUTE_BRIEFS_FOLDER_ID",
    "DECK_TEMPLATE": "PASTE_DECK_TEMPLATE_PRESENTATION_ID",
}

# ---------------------------------------------------------------- wf assembly
class WF:
    def __init__(self, name, description):
        self.name, self.description = name, description
        self.nodes, self.connections = [], {}

    def add(self, node):
        self.nodes.append(node)
        return node["name"]

    def wire(self, src, dst, src_out=0):
        c = self.connections.setdefault(src, {"main": []})
        while len(c["main"]) <= src_out:
            c["main"].append([])
        c["main"][src_out].append({"node": dst, "type": "main", "index": 0})

    def chain(self, *names):
        for a, b in zip(names, names[1:]):
            self.wire(a, b)

    def write(self, filename):
        wf = {"name": self.name, "nodes": self.nodes, "connections": self.connections,
              "settings": {"executionOrder": "v1"}, "meta": {"description": self.description}}
        path = os.path.join(HERE, filename)
        with open(path, "w") as f:
            json.dump(wf, f, indent=2, ensure_ascii=False)
        print(f"Wrote {filename}  ({len(self.nodes)} nodes)")
        return path

# ---------------------------------------------------------------- node factory
def nid(name):
    return name.replace(" ", "_").replace(":", "").replace("/", "_")[:30]

def exec_trigger(x=0, y=300):
    return {"parameters": {}, "id": "input", "name": "Input",
            "type": "n8n-nodes-base.executeWorkflowTrigger", "typeVersion": 1, "position": [x, y]}

def manual_trigger(name="Run", x=0, y=300):
    return {"parameters": {}, "id": nid(name), "name": name,
            "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [x, y]}

def schedule_trigger(name, hours=None, cron=None, x=0, y=300):
    if cron:
        rule = {"interval": [{"field": "cronExpression", "expression": cron}]}
    else:
        rule = {"interval": [{"field": "hours", "hoursInterval": hours}]}
    return {"parameters": {"rule": rule}, "id": nid(name), "name": name,
            "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [x, y]}

def code(name, js, x, y):
    return {"parameters": {"jsCode": js}, "id": nid(name), "name": name,
            "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x, y]}

def http(name, url, x, y, method="GET", cred=None, cred_type=None, headers=None,
         qs=None, json_body=None, response_file=False):
    p = {"method": method, "url": url, "options": {}}
    if cred_type:
        p["authentication"] = "predefinedCredentialType"
        p["nodeCredentialType"] = cred_type
    elif cred:
        p["authentication"] = "genericCredentialType"
        p["genericAuthType"] = "httpHeaderAuth"
    if headers:
        p["sendHeaders"] = True
        p["headerParameters"] = {"parameters": [{"name": k, "value": v} for k, v in headers]}
    if qs:
        p["sendQuery"] = True
        p["queryParameters"] = {"parameters": [{"name": k, "value": v} for k, v in qs]}
    if json_body is not None:
        p["sendBody"] = True
        p["specifyBody"] = "json"
        p["jsonBody"] = json_body
    if response_file:
        p["options"]["response"] = {"response": {"responseFormat": "file"}}
    node = {"parameters": p, "id": nid(name), "name": name,
            "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x, y]}
    if cred:
        node["credentials"] = cred
    elif cred_type == "quickBooksOAuth2Api":
        node["credentials"] = QBO_CRED
    elif cred_type == "anthropicApi":
        node["credentials"] = ANTHROPIC_CRED
    elif cred_type == "googleDriveOAuth2Api":
        node["credentials"] = GOOGLE_DRIVE_CRED
    elif cred_type == "googleDocsOAuth2Api":
        node["credentials"] = GOOGLE_DOCS_CRED
    return node

def sheets_read(name, doc_id, tab, x, y, filters=None):
    p = {"resource": "sheet", "operation": "read",
         "documentId": {"__rl": True, "mode": "id", "value": doc_id},
         "sheetName": {"__rl": True, "mode": "name", "value": tab}, "options": {}}
    if filters:
        p["filtersUI"] = {"values": [{"lookupColumn": k, "lookupValue": v} for k, v in filters]}
    return {"parameters": p, "id": nid(name), "name": name,
            "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": [x, y],
            "credentials": GOOGLE_SHEETS_CRED}

def sheets_append(name, doc_id, tab, x, y):
    p = {"resource": "sheet", "operation": "append",
         "documentId": {"__rl": True, "mode": "id", "value": doc_id},
         "sheetName": {"__rl": True, "mode": "name", "value": tab},
         "columns": {"mappingMode": "autoMapInputData", "value": {}}, "options": {}}
    return {"parameters": p, "id": nid(name), "name": name,
            "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": [x, y],
            "credentials": GOOGLE_SHEETS_CRED}

def sheets_update(name, doc_id, tab, x, y):
    p = {"resource": "sheet", "operation": "update",
         "documentId": {"__rl": True, "mode": "id", "value": doc_id},
         "sheetName": {"__rl": True, "mode": "name", "value": tab},
         "columns": {"mappingMode": "autoMapInputData", "value": {},
                      "matchingColumns": ["row_number"]}, "options": {}}
    return {"parameters": p, "id": nid(name), "name": name,
            "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": [x, y],
            "credentials": GOOGLE_SHEETS_CRED}

def gmail_send(name, to, subject, message, x, y):
    return {"parameters": {"resource": "message", "operation": "send", "sendTo": to,
                           "subject": subject, "message": message, "options": {}},
            "id": nid(name), "name": name, "type": "n8n-nodes-base.gmail",
            "typeVersion": 2, "position": [x, y], "credentials": GMAIL_CRED}

def qbo_url(path):
    """QBO API v3 url for the client realm carried in the Input context."""
    return "=https://quickbooks.api.intuit.com/v3/company/{{ $('Input').first().json.qbo_realm_id }}" + path

def qbo_get(name, path, x, y, qs=None):
    q = [("minorversion", "73")] + (qs or [])
    return http(name, qbo_url(path), x, y, cred_type="quickBooksOAuth2Api",
                headers=[("Accept", "application/json")], qs=q)

# ---------------------------------------------------------------- Claude trio
def claude_trio(wf, key, build_js, x, y, prev, out_key, max_tokens=8000, thinking=False):
    """Adds Build -> Claude -> Parse and wires them after `prev`. Returns parse node name."""
    b = wf.add(code(f"Build request: {key}", build_js, x, y))
    body = "={{ JSON.stringify($json.payload) }}"
    c = wf.add(http(f"Claude: {key}", "https://api.anthropic.com/v1/messages", x + 220, y,
                    method="POST", cred_type="anthropicApi",
                    headers=[("anthropic-version", "2023-06-01")], json_body=body))
    parse_js = (
        "// Structured outputs: the JSON arrives as a string in content[0].text.\n"
        "const text = $json.content?.[0]?.text ?? '{}';\n"
        "let out; try { out = JSON.parse(text); } catch (e) { out = { parse_error: true, raw: text }; }\n"
        "const ctx = $('Input').first().json;\n"
        f"return [{{ json: {{ ...ctx, {out_key}: out }} }}];\n")
    p = wf.add(code(f"Parse: {key}", parse_js, x + 440, y))
    wf.chain(prev, b, c, p)
    _ = (max_tokens, thinking)  # documented in the build_js payloads themselves
    return p

def payload_js(system_prompt, schema, user_expr_js, max_tokens=8000, thinking=False):
    """JS that builds an Anthropic Messages payload. `user_expr_js` is a JS expression string."""
    extra = "  thinking: { type: 'adaptive' },\n" if thinking else ""
    return (
        "const ctx = $('Input').first().json;\n"
        "const userContent = " + user_expr_js + ";\n"
        "const payload = {\n"
        "  model: 'claude-opus-4-8',\n"
        f"  max_tokens: {max_tokens},\n" + extra +
        "  system: " + json.dumps(system_prompt) + ",\n"
        "  messages: [{ role: 'user', content: userContent }],\n"
        "  output_config: { effort: 'high', format: { type: 'json_schema', schema: "
        + json.dumps(schema) + " } }\n"
        "};\n"
        "return [{ json: { ...$json, payload } }];\n")

# ---------------------------------------------------------------- prompts (from Claude-Prompts.md)
P = {}

P["digest"] = dict(
    system=("You are a tax-firm assistant preparing an internal briefing for a CPA before a "
            "quarterly client meeting. You are given the client's email/communication threads "
            "since the last meeting. Produce a factual digest for the preparer. Do not give "
            "advice, do not invent facts, and do not infer commitments that are not stated. "
            "If something is ambiguous, mark it as \"unclear\". Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["firm_commitments", "client_commitments", "open_questions", "changes", "unresolved_threads", "sentiment"],
            "properties": {
                "firm_commitments": {"type": "array", "items": {"type": "string"}},
                "client_commitments": {"type": "array", "items": {"type": "string"}},
                "open_questions": {"type": "array", "items": {"type": "string"}},
                "changes": {"type": "array", "items": {"type": "string"}},
                "unresolved_threads": {"type": "array", "items": {"type": "string"}},
                "sentiment": {"type": "string", "enum": ["positive", "neutral", "concerned", "frustrated", "unclear"]}}})

P["recap"] = dict(
    system=("You are preparing a CPA for a quarterly client meeting. You are given the prior "
            "meeting's transcript/summary and the current list of Karbon work items for the "
            "client. For every promise or action item raised in the prior meeting, determine "
            "its status by cross-referencing the Karbon work items: Done, Pending, or Blocked. "
            "Only mark Done when a work item clearly shows completion. If you cannot tell, use "
            "Pending and say why. Do not invent work items. Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["promises", "strategies_discussed_not_implemented", "client_questions_raised"],
            "properties": {
                "promises": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["item", "owner", "status", "evidence"],
                    "properties": {"item": {"type": "string"},
                                    "owner": {"type": "string", "enum": ["firm", "client", "unclear"]},
                                    "status": {"type": "string", "enum": ["done", "pending", "blocked"]},
                                    "evidence": {"type": "string"}}}},
                "strategies_discussed_not_implemented": {"type": "array", "items": {"type": "string"}},
                "client_questions_raised": {"type": "array", "items": {"type": "string"}}}})

P["taxpos"] = dict(
    system=("You are extracting structured tax data from a client's tax returns and prior "
            "tax plans for internal use by a CPA. Extract only values that are explicitly "
            "present in the documents. Never estimate or fill gaps — use null for anything "
            "not found. This feeds a tax projection, so accuracy matters more than "
            "completeness. Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["tax_year", "agi", "taxable_income", "marginal_rate", "effective_rate", "carryforwards", "elections", "estimates_paid", "safe_harbor_target", "notes"],
            "properties": {
                "tax_year": {"type": ["string", "null"]},
                "agi": {"type": ["number", "null"]},
                "taxable_income": {"type": ["number", "null"]},
                "marginal_rate": {"type": ["number", "null"]},
                "effective_rate": {"type": ["number", "null"]},
                "carryforwards": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["type", "amount"],
                    "properties": {"type": {"type": "string"}, "amount": {"type": ["number", "null"]}}}},
                "elections": {"type": "array", "items": {"type": "string"}},
                "estimates_paid": {"type": ["number", "null"]},
                "safe_harbor_target": {"type": ["number", "null"]},
                "notes": {"type": "array", "items": {"type": "string"}}}})

P["inventory"] = dict(
    system=("You are triaging a tax client's document folder before a quarterly meeting. You "
            "are given the file listing of the client's Drive folder and, when available, the "
            "contents of their payment (PMT) schedule. Identify which files are relevant to "
            "this meeting, and summarize the payment schedule status: what is scheduled, what "
            "has been paid, and what is upcoming — so the brief can answer \"does the payments "
            "coordinator know what to pay?\". Do not invent files or payments. Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["relevant_files", "pmt_status", "pmt_upcoming", "gaps"],
            "properties": {
                "relevant_files": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["name", "why_relevant"],
                    "properties": {"name": {"type": "string"}, "why_relevant": {"type": "string"}}}},
                "pmt_status": {"type": "string"},
                "pmt_upcoming": {"type": "array", "items": {"type": "string"}},
                "gaps": {"type": "array", "items": {"type": "string"}}}})

P["payroll"] = dict(
    system=("You are extracting payroll data from uploaded pay stub documents for a CPA's tax "
            "projection. Extract per employee: gross pay YTD, federal withholding YTD, state "
            "withholding YTD, pay period, and pay frequency if visible. Extract only what is "
            "explicitly on the stubs; use null for anything not found. Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["employees", "notes"],
            "properties": {
                "employees": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["name", "gross_ytd", "federal_withholding_ytd", "state_withholding_ytd", "period_end"],
                    "properties": {"name": {"type": ["string", "null"]},
                                    "gross_ytd": {"type": ["number", "null"]},
                                    "federal_withholding_ytd": {"type": ["number", "null"]},
                                    "state_withholding_ytd": {"type": ["number", "null"]},
                                    "period_end": {"type": ["string", "null"]}}}},
                "notes": {"type": "array", "items": {"type": "string"}}}})

P["screener"] = dict(
    system=("You are screening a curated tax-strategy library against one client's current "
            "data to surface planning opportunities for a CPA to evaluate. You are given: "
            "(1) the Strategy Library (each row: name, category, trigger conditions, savings "
            "heuristic, authority, risk rating, review status); (2) the client's data "
            "(financials, tax position, profile, questionnaire answers); (3) the client's "
            "strategy status (already implemented or previously rejected).\n"
            "Rules:\n"
            "- ONLY consider strategies whose review_status is \"Firm-Approved\". Ignore Draft rows.\n"
            "- SKIP any strategy already implemented or previously rejected for this client.\n"
            "- A strategy is a candidate ONLY if the client's data actually satisfies its "
            "trigger conditions. Do not force matches.\n"
            "- Estimate annual savings using the row's heuristic and the client's real "
            "numbers. Show your inputs. If you can't compute a number, give a range and "
            "mark it \"rough\".\n"
            "- Rank candidates by estimated savings.\n"
            "- This is a screen, not advice. Every candidate must be validated by the "
            "professional (and, for Moderate/Aggressive risk, a Blue J-backed memo) before "
            "it reaches the client. Never present a strategy as recommended.\n"
            "Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["candidates", "skipped"],
            "properties": {
                "candidates": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["strategy_id", "strategy_name", "risk_rating", "why_it_triggers", "estimated_annual_savings", "savings_basis", "requires_memo", "confidence"],
                    "properties": {"strategy_id": {"type": "string"},
                                    "strategy_name": {"type": "string"},
                                    "risk_rating": {"type": "string", "enum": ["Conservative", "Moderate", "Aggressive"]},
                                    "why_it_triggers": {"type": "string"},
                                    "estimated_annual_savings": {"type": ["number", "null"]},
                                    "savings_basis": {"type": "string"},
                                    "requires_memo": {"type": "boolean"},
                                    "confidence": {"type": "string", "enum": ["high", "medium", "rough"]}}}},
                "skipped": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["strategy_name", "reason"],
                    "properties": {"strategy_name": {"type": "string"},
                                    "reason": {"type": "string", "enum": ["already_implemented", "previously_rejected", "triggers_not_met", "draft_row"]}}}}}})

P["estimate"] = dict(
    system=("You are computing quarterly estimated tax payments for a CPA to review, from a "
            "client's projected income and withholdings. Show every input and every step so "
            "the preparer can audit the math. Use the provided rates and the state's "
            "quarterly schedule. When you must annualize partial-year data, state the factor "
            "you used and flag it as a judgment call for the preparer. If the client has a "
            "C-corp, also compute the \"with vs. without C-corp\" comparison. Never present "
            "the numbers as final — they are a draft for professional review. Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["projected_income", "projected_net_profit", "annualization_notes", "federal_liability", "state_liability", "total_withholdings", "quarterly_payments", "entity_comparison", "anomalies"],
            "properties": {
                "projected_income": {"type": "number"},
                "projected_net_profit": {"type": "number"},
                "annualization_notes": {"type": "array", "items": {"type": "string"}},
                "federal_liability": {"type": "number"},
                "state_liability": {"type": "number"},
                "total_withholdings": {"type": "number"},
                "quarterly_payments": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["quarter", "federal", "state", "due_date"],
                    "properties": {"quarter": {"type": "string"}, "federal": {"type": "number"},
                                    "state": {"type": "number"}, "due_date": {"type": "string"}}}},
                "entity_comparison": {"type": "object", "additionalProperties": False,
                    "required": ["applicable", "with_ccorp_total", "without_ccorp_total", "savings"],
                    "properties": {"applicable": {"type": "boolean"},
                                    "with_ccorp_total": {"type": ["number", "null"]},
                                    "without_ccorp_total": {"type": ["number", "null"]},
                                    "savings": {"type": ["number", "null"]}}},
                "anomalies": {"type": "array", "items": {"type": "string"}}}})

P["scorecard"] = dict(
    system=("You are building a 4-metric client scorecard and a short financial review for a "
            "quarterly meeting. Compute revenue (last 12 mo vs prior 12 mo), gross and net "
            "profit margin, and owner take-home (salary + distributions + benefits) for both "
            "periods. Then write a brief narrative that explains WHAT DRIVES the changes. "
            "Frame the story around tax and owner outcomes, not CFO-level detail. Flag any "
            "figure that looks like an accounting artifact rather than real performance. "
            "Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["revenue", "gross_margin", "net_margin", "owner_take_home", "narrative", "artifacts"],
            "properties": {
                "revenue": {"type": "object", "additionalProperties": False,
                    "required": ["current", "prior", "pct_change"],
                    "properties": {"current": {"type": "number"}, "prior": {"type": "number"}, "pct_change": {"type": "number"}}},
                "gross_margin": {"type": "object", "additionalProperties": False,
                    "required": ["current", "prior"],
                    "properties": {"current": {"type": "number"}, "prior": {"type": "number"}}},
                "net_margin": {"type": "object", "additionalProperties": False,
                    "required": ["current", "prior"],
                    "properties": {"current": {"type": "number"}, "prior": {"type": "number"}}},
                "owner_take_home": {"type": "object", "additionalProperties": False,
                    "required": ["current", "prior"],
                    "properties": {"current": {"type": "number"}, "prior": {"type": "number"}}},
                "narrative": {"type": "string"},
                "artifacts": {"type": "array", "items": {"type": "string"}}}})

P["brief"] = dict(
    system=("You are assembling the internal Meeting Brief a CPA will use to run a quarterly "
            "client meeting. You are given the outputs of every upstream step (email digest, "
            "last-meeting recap, books health, tax estimate, strategy screener, scorecard, "
            "Karbon items, questionnaire answers, and the preparer's own notes). Produce a "
            "single structured brief with the nine sections in the schema. Write for the "
            "preparer: concise, specific, decision-ready. Lead each section with what matters "
            "most. In \"Strategy Opportunities\", present the screener's candidates with their "
            "estimated savings and mark which need a Blue J memo — as options to evaluate, "
            "never as recommendations. Frame the financial review inside the tax story. Do "
            "not introduce facts that aren't in the inputs. Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["executive_summary", "since_last_meeting", "follow_up_items", "financial_review", "books_health", "tax_position", "strategy_opportunities", "key_talking_points", "questions_for_client"],
            "properties": {
                "executive_summary": {"type": "array", "items": {"type": "string"}},
                "since_last_meeting": {"type": "string"},
                "follow_up_items": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["item", "owner"],
                    "properties": {"item": {"type": "string"}, "owner": {"type": "string"}}}},
                "financial_review": {"type": "string"},
                "books_health": {"type": "string"},
                "tax_position": {"type": "string"},
                "strategy_opportunities": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["strategy", "estimated_savings", "needs_memo"],
                    "properties": {"strategy": {"type": "string"},
                                    "estimated_savings": {"type": ["number", "null"]},
                                    "needs_memo": {"type": "boolean"}}}},
                "key_talking_points": {"type": "array", "items": {"type": "string"}},
                "questions_for_client": {"type": "array", "items": {"type": "string"}}}})

P["actions"] = dict(
    system=("You are processing the transcript of a completed quarterly tax-planning meeting. "
            "Extract every action item with its owner (firm or client), a suggested deadline, "
            "and priority. Also produce a 5-sentence meeting summary and note any tax "
            "strategies discussed that should be proposed for the firm's strategy library. "
            "Do not invent items. Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["summary", "action_items", "strategies_discussed"],
            "properties": {
                "summary": {"type": "string"},
                "action_items": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["item", "owner", "deadline", "priority"],
                    "properties": {"item": {"type": "string"},
                                    "owner": {"type": "string", "enum": ["firm", "client"]},
                                    "deadline": {"type": ["string", "null"]},
                                    "priority": {"type": "string", "enum": ["high", "medium", "low"]}}}},
                "strategies_discussed": {"type": "array", "items": {"type": "string"}}}})

P["reclass"] = dict(
    system=("You are proposing QuickBooks categorizations for uncategorized transactions, for "
            "a human to approve. For each transaction propose the most likely expense/income "
            "account from the client's chart of accounts, with confidence. Never invent "
            "transactions; if unsure, use low confidence. These proposals are applied ONLY "
            "after human approval. Output only the JSON schema."),
    schema={"type": "object", "additionalProperties": False,
            "required": ["proposals"],
            "properties": {
                "proposals": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "required": ["txn_id", "txn_type", "date", "description", "amount", "proposed_account", "confidence"],
                    "properties": {"txn_id": {"type": "string"},
                                    "txn_type": {"type": "string"},
                                    "date": {"type": ["string", "null"]},
                                    "description": {"type": "string"},
                                    "amount": {"type": ["number", "null"]},
                                    "proposed_account": {"type": "string"},
                                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]}}}}}})
