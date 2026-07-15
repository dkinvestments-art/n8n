# Video Watch n8n Workflow - Setup

`n8n-workflow.json` in this skill folder is an importable n8n workflow that
does the same job as the Claude Code skill, but runs inside a self-hosted
n8n instance so it can be triggered automatically (e.g. from a form, a
Telegram bot, or a scheduled check against a playlist).

## Import

In n8n: **Workflows -> Import from File** and select `n8n-workflow.json`.

## Requirements

- **Self-hosted n8n** with shell access, since the workflow uses the
  **Execute Command** node. This will not work on n8n Cloud, which disables
  arbitrary command execution.
- **`yt-dlp`** installed on the n8n host (`pip install -U yt-dlp`). This is
  what actually fetches captions/subtitles for YouTube, Vimeo, and other
  yt-dlp-supported hosts.
- **An Anthropic credential** attached to the "Anthropic Chat Model" node
  (Settings -> Credentials -> Anthropic API).
- The n8n host process needs **filesystem access to the Obsidian vault
  path** used in the "Save to Obsidian Vault" node - if n8n runs in Docker,
  mount the vault directory as a volume.

## Nodes

| Node | What it does |
|---|---|
| Video Input | Set `videoUrl`, `vaultPath`, `folder` before running |
| Fetch Transcript & Metadata | Runs `yt-dlp` to pull captions + video metadata |
| Parse Transcript | Cleans the raw VTT captions into plain text |
| Summarize Video | Basic LLM Chain - produces Main Points / Nuances / Actionable Insights |
| Anthropic Chat Model | Language model backing the chain |
| Build Note | Assembles the final markdown note (frontmatter + summary + transcript) |
| Convert Note to File | Turns the markdown string into a binary file |
| Save to Obsidian Vault | Writes the `.md` file to `vaultPath/folder/title.md` |

## Known limitations

- Skool community videos are often embedded via a proprietary player. If
  `yt-dlp` can't extract subtitles for a given URL, "Parse Transcript" falls
  back to a placeholder telling you to paste the transcript manually -
  re-run from the "Summarize Video" node after fixing the `transcript`
  field on "Parse Transcript"'s output.
- `yt-dlp --dump-json` only reads the first video if given a playlist URL.
  For playlists, loop over individual video URLs instead (e.g. with a
  Split In Batches node feeding one URL at a time into "Video Input").
