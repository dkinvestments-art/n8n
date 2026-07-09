# Strategy Library — Import Files

Seed content for the Tax Strategy Screener (Developer Requirements
Specification, Sub-Workflow 17).

## Files

| File | Becomes | Purpose |
|------|---------|---------|
| `Strategy-Library.csv` | **"Strategy Library"** tab | Master library — 36 seeded strategies across 10 categories, one row per strategy |
| `Client-Strategy-Status-Template.csv` | **"Client Strategy Status"** tab | Per-client tracking (client × strategy): implemented / rejected / candidate. Delete the EXAMPLE rows after import |

A third tab, **"Proposed Strategies"**, starts empty — the AI discovery,
transcript-mining, and law-change-sweep intake paths write Draft
suggestions there.

## Import Steps (Google Sheets)

1. Create a new Google Sheet named `Tax Strategy Library`
2. File → Import → Upload → `Strategy-Library.csv` → "Replace current sheet"; rename the tab **Strategy Library**
3. Add a tab, import `Client-Strategy-Status-Template.csv` the same way; rename it **Client Strategy Status**
4. Add an empty tab named **Proposed Strategies** (same columns as Strategy Library)
5. Add data validation:
   - `risk_rating`: Conservative / Moderate / Aggressive
   - `review_status`: "Draft — pending Firm review" / "Firm-Approved" / "Retired"
   - `status` (client tab): implemented / candidate / rejected
6. Link the sheet ID into the n8n workflow credentials/config per the developer setup guide

## IMPORTANT — Before First Use

**Every seed row ships as `Draft — pending Firm review`.** The screener
only evaluates **Firm-Approved** rows against clients, so nothing screens
until a qualified professional at the Firm reviews each row and flips its
status. Budget ~30-45 minutes to review all 36. During that review:

- Verify each authority citation against current law — several rows
  reference OBBBA (2025) provisions with vintage-specific rules and
  sunset dates (ST-006 QSBS, ST-013 bonus, ST-017 OZ, ST-028 R&D,
  ST-030 clean energy, ST-031 charitable floor)
- Adjust savings heuristics to the Firm's preferred assumptions
- Re-rate risk levels to the Firm's own tolerance — ratings shipped here
  are starting points, not conclusions
- Remember the standing guardrails: Aggressive-rated strategies always
  require a Blue J-validated memo AND explicit preparer sign-off before
  appearing in any client brief; strategies resembling IRS
  listed/reportable transactions are excluded by policy

## Maintenance

- New strategies enter via the four intake paths (manual add, AI
  discovery, transcript mining, quarterly law-change sweep) as Draft rows
- Retire rows (don't delete) when law changes kill a strategy — set
  `review_status` to Retired so per-client history is preserved

---

*This library is planning-support content, not tax advice. Savings
heuristics are estimates for screening only. A qualified professional
must validate every strategy against the client's facts and current law
before implementation.*
