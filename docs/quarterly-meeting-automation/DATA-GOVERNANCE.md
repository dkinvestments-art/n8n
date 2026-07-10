# Data Governance — Astute Advisors

**Status:** Binding rule for this project. Applies to Claude, the developer,
and all automation workflows.

## Rule 1 — Astute Advisors data lives only on Astute infrastructure

All Astute Advisors files, client data, and tax data must live on **Karen's
Astute Advisors Google Workspace / Google Drive** — never on any personal
account (e.g., dkinvestments0@gmail.com) or any other personal/third-party
storage.

This covers, without limitation:
- Client files (financials, tax returns, PMT schedules, scorecards)
- The Client Profile Matrix, Strategy Library, Client Strategy Status, run
  logs, and any other automation configuration sheets that reference clients
- Meeting Briefs, presentation decks, and any generated deliverables
- Client emails and meeting transcripts ingested by the workflows

## Rule 2 — All automation credentials are Karen's Astute Advisors accounts

Every credential the n8n workflows use (Google Workspace, QuickBooks Online,
Karbon, Fathom, Gamma, etc.) must be authenticated as **Astute Advisors
accounts owned/controlled by Karen** — not personal accounts. This keeps every
read and write inside Astute-controlled infrastructure and consistent with the
firm's IRS §7216 / GLBA obligations (see `04-IRS-Compliance-Guide.md`).

## Rule 3 — Personal accounts never touch Astute data

The personal Google account connected to ad-hoc assistant sessions
(dkinvestments0@gmail.com) must not be used to create, store, or process any
Astute Advisors file. If an assistant session is only connected to a personal
account, Astute deliverables are produced as local/repo files and handed off —
they are NOT written to the personal Drive.

---

*Recorded 2026-07-10 at the firm's direction. Karen also asked that this rule
be kept in her Obsidian memory; mirror it there.*
