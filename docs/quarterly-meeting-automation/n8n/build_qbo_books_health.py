#!/usr/bin/env python3
"""Worked example: a fully-wired n8n workflow that pulls QuickBooks Online data
(A/R aging, A/P aging, Balance Sheet, recent transactions) and calls Claude with
the Books Health prompt to produce the "Books Health" brief section.

This is the concrete pattern the developer pattern-matches for the other
ingestion+AI nodes. Real QBO API v3 endpoints and a real Anthropic Messages API
call; needs Karen's Astute QuickBooks + Anthropic credentials selected on import,
plus the client's realmId in the Config node.

Run:  python3 build_qbo_books_health.py
Emits: Astute-QBO-Books-Health.workflow.json
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Astute-QBO-Books-Health.workflow.json")

QBO_CRED = {"quickBooksOAuth2Api": {"id": "REPLACE_ASTUTE_QBO", "name": "Karen Astute Advisors QuickBooks"}}
ANTHROPIC_CRED = {"anthropicApi": {"id": "REPLACE_ASTUTE_ANTHROPIC", "name": "Karen Astute Advisors Anthropic"}}

SYSTEM_PROMPT = (
    "You are a CPA's assistant producing a \"Books Health\" section for a quarterly "
    "meeting brief. You are given QuickBooks data: A/R aging, A/P aging, balance sheet, "
    "and a list of recent transactions. Summarize the state of the books plainly. Flag: "
    "stale or large uncategorized items, aged receivables or payables, negative or unusual "
    "balances, and anything that would make the financials unreliable for tax projection. "
    "Propose a likely category for each uncategorized transaction, but mark each proposal "
    "as needs_review=true — a human approves before anything is applied. Do not invent "
    "transactions. Output only the JSON schema."
)

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["close_status", "summary", "flags", "uncategorized_proposals", "ar_summary", "ap_summary"],
    "properties": {
        "close_status": {"type": "string", "enum": ["clean", "minor_issues", "needs_attention", "not_reliable"]},
        "summary": {"type": "string"},
        "flags": {"type": "array", "items": {"type": "string"}},
        "uncategorized_proposals": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["transaction", "amount", "proposed_category", "confidence", "needs_review"],
            "properties": {
                "transaction": {"type": "string"},
                "amount": {"type": ["number", "null"]},
                "proposed_category": {"type": "string"},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                "needs_review": {"type": "boolean"},
            }}},
        "ar_summary": {"type": "string"},
        "ap_summary": {"type": "string"},
    },
}

nodes, connections = [], {}
def add(n): nodes.append(n); return n["name"]
def wire(a, b):
    connections.setdefault(a, {"main": [[]]})
    connections[a]["main"][0].append({"node": b, "type": "main", "index": 0})

def qbo_report(name, report, x, y):
    return add({"parameters": {
        "method": "GET",
        "url": f"=={{{{ $('Config').first().json.qbo_base }}}}/v3/company/{{{{ $('Config').first().json.realmId }}}}/reports/{report}",
        "authentication": "predefinedCredentialType", "nodeCredentialType": "quickBooksOAuth2Api",
        "sendQuery": True, "queryParameters": {"parameters": [{"name": "minorversion", "value": "73"}]},
        "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Accept", "value": "application/json"}]},
        "options": {}},
        "id": name.replace(" ", "_")[:28], "name": name,
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x, y],
        "credentials": QBO_CRED})

# 1. Manual trigger
trig = add({"parameters": {}, "id": "trigger", "name": "Run books health check",
            "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 300]})

# 2. Config
cfg = add({"parameters": {"assignments": {"assignments": [
        {"id": "a1", "name": "client_name", "type": "string", "value": "PASTE_CLIENT_NAME"},
        {"id": "a2", "name": "realmId", "type": "string", "value": "PASTE_CLIENT_QBO_REALM_ID"},
        {"id": "a3", "name": "qbo_base", "type": "string", "value": "https://quickbooks.api.intuit.com"}]},
        "options": {}},
    "id": "config", "name": "Config",
    "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [220, 300]})
wire(trig, cfg)

# 3-5. QBO reports (sequential pass-through)
ar = qbo_report("QBO: A/R aging", "AgedReceivables", 440, 300)
ap = qbo_report("QBO: A/P aging", "AgedPayables", 660, 300)
bs = qbo_report("QBO: Balance Sheet", "BalanceSheet", 880, 300)
wire(cfg, ar); wire(ar, ap); wire(ap, bs)

# 6. QBO transactions query (Purchases sample)
txn = add({"parameters": {
    "method": "GET",
    "url": "=={{ $('Config').first().json.qbo_base }}/v3/company/{{ $('Config').first().json.realmId }}/query",
    "authentication": "predefinedCredentialType", "nodeCredentialType": "quickBooksOAuth2Api",
    "sendQuery": True, "queryParameters": {"parameters": [
        {"name": "minorversion", "value": "73"},
        {"name": "query", "value": "SELECT * FROM Purchase ORDERBY TxnDate DESC MAXRESULTS 50"}]},
    "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Accept", "value": "application/json"}]},
    "options": {}},
    "id": "qbo_txn", "name": "QBO: recent transactions",
    "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1100, 300],
    "credentials": QBO_CRED})
wire(bs, txn)

# 7. Build Claude request
build_code = (
    "// Assemble the QBO pulls and build the Anthropic Messages API request.\n"
    "const client = $('Config').first().json.client_name;\n"
    "const ar = JSON.stringify($('QBO: A/R aging').first().json);\n"
    "const ap = JSON.stringify($('QBO: A/P aging').first().json);\n"
    "const bs = JSON.stringify($('QBO: Balance Sheet').first().json);\n"
    "const txns = JSON.stringify($('QBO: recent transactions').first().json);\n"
    "const userContent =\n"
    "  `Client: ${client}\\n\\n--- A/R AGING ---\\n${ar}\\n\\n--- A/P AGING ---\\n${ap}` +\n"
    "  `\\n\\n--- BALANCE SHEET ---\\n${bs}\\n\\n--- RECENT TRANSACTIONS ---\\n${txns}`;\n"
    "const payload = {\n"
    "  model: 'claude-opus-4-8',\n"
    "  max_tokens: 8000,\n"
    "  system: " + json.dumps(SYSTEM_PROMPT) + ",\n"
    "  messages: [{ role: 'user', content: userContent }],\n"
    "  output_config: { effort: 'high', format: { type: 'json_schema', schema: " + json.dumps(SCHEMA) + " } }\n"
    "};\n"
    "return [{ json: { payload } }];\n"
)
build = add({"parameters": {"jsCode": build_code},
    "id": "build", "name": "Build Claude request",
    "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [1320, 300]})
wire(txn, build)

# 8. Anthropic call
claude = add({"parameters": {
    "method": "POST", "url": "https://api.anthropic.com/v1/messages",
    "authentication": "predefinedCredentialType", "nodeCredentialType": "anthropicApi",
    "sendHeaders": True, "headerParameters": {"parameters": [{"name": "anthropic-version", "value": "2023-06-01"}]},
    "sendBody": True, "specifyBody": "json", "jsonBody": "={{ JSON.stringify($json.payload) }}",
    "options": {}},
    "id": "claude", "name": "Claude: Books Health",
    "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1540, 300],
    "credentials": ANTHROPIC_CRED})
wire(build, claude)

# 9. Parse result
parse = add({"parameters": {"jsCode":
    "// Anthropic returns the JSON as a string in content[0].text (structured outputs).\n"
    "const text = $json.content?.[0]?.text ?? '{}';\n"
    "let booksHealth;\n"
    "try { booksHealth = JSON.parse(text); } catch (e) { booksHealth = { parse_error: true, raw: text }; }\n"
    "return [{ json: { books_health: booksHealth } }];\n"},
    "id": "parse", "name": "Parse Books Health",
    "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [1760, 300]})
wire(claude, parse)

wf = {"name": "Astute — QBO Books Health (worked example)", "nodes": nodes,
      "connections": connections, "settings": {"executionOrder": "v1"},
      "meta": {"description": "Worked example: pull QBO A/R + A/P aging, Balance Sheet, and recent "
               "transactions, then call Claude with the Books Health prompt to produce the brief's "
               "Books Health section. Select Karen's Astute QuickBooks and Anthropic credentials; "
               "set the client's realmId in Config."}}

with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
print(f"Wrote {OUT}")
print(f"Nodes: {len(nodes)}")
