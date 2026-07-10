# n8n Seed Workflow — Automation Sheets (Astute Advisors Drive)

This folder contains an **importable n8n workflow** that creates the three
automation Google Sheets directly in **Karen's Astute Advisors Google Drive**,
authenticated as her Astute account. Per `../DATA-GOVERNANCE.md`, nothing here
touches any personal account.

## What it creates

| Sheet | Seeded content |
|-------|----------------|
| **Tax Strategy Library** | All 36 strategies (from `../strategy-library/Strategy-Library.csv`) |
| **Client Strategy Status** | Header row (per-client tracking; ready for data) |
| **Client Profile Matrix** | Headers + one EXAMPLE row (delete after review) |

## Files

- `Astute-Seed-Automation-Sheets.workflow.json` — the importable workflow
- `Client-Profile-Matrix.csv`, `Client-Strategy-Status.csv` — source data (also embedded in the workflow)
- `build_seed_workflow.py` — regenerates the workflow JSON from the CSVs (run if you edit the CSVs)

The workflow is **self-contained**: each CSV is embedded (base64) inside a Code
node and parsed at run time, so there are no external file dependencies.

## Import & run (5 minutes, done inside Karen's n8n)

1. **Import**: in Karen's n8n → Workflows → Import from File → choose
   `Astute-Seed-Automation-Sheets.workflow.json`.
2. **Credential**: on each Google node (6 total — the Create/Move/Append nodes),
   select **Karen's Astute Advisors Google credential**. If it doesn't exist
   yet, create one OAuth credential signed in as her Astute Workspace account
   and select it on all of them. The JSON ships with a placeholder credential
   named "Karen Astute Advisors Google" as a reminder.
3. **Folder**: create (or pick) an **Automations** folder in Karen's Astute
   Drive, copy its folder ID from the URL
   (`drive.google.com/drive/folders/<THIS_ID>`), and paste it into the
   **Config (set Astute folder ID)** node.
4. **Run once** with "Run once to seed sheets". The three sheets appear in the
   Astute Automations folder.
5. **Tidy up**: delete the single blank row in Client Strategy Status and the
   EXAMPLE row in Client Profile Matrix.

## Important notes

- **Governance**: because every Google node uses Karen's Astute credential and
  the target is her Astute folder, all three sheets are created and owned on
  Astute infrastructure. The personal account is never used.
- **Validation run**: this workflow was authored and its embedded data/parsing
  were verified, but it could **not** be executed against Karen's live n8n from
  the build environment. The developer should do one validation run and confirm
  the Google **Sheets create / Drive move / Sheets append** node parameters
  match the installed n8n version (node schemas occasionally shift between
  versions). The embedded CSV data and Code-node parsing are confirmed correct
  (Library = 36 rows, Profile = 1 example row).
- **Re-running** creates fresh copies each time (it does not overwrite). Run
  once; if you need to re-seed, delete the prior sheets first.
- **Editing the library later**: edit the CSV, re-run `build_seed_workflow.py`,
  re-import — or just edit the live Google Sheet directly (the ongoing intake
  paths in the screener spec write there anyway).
