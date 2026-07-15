---
name: video-watch
description: Watch/transcribe a video (YouTube, Skool community, Vimeo, etc.), summarize it, and save the notes into the user's Obsidian vault. Use when the user shares a video link and asks to watch it, summarize it, or add it to their notes/knowledge base/Education folder.
---

# Video Watch Skill

Turn a video link into a saved Obsidian note containing the transcript plus
a structured summary: main points, nuances the speaker emphasized, and
concrete actionable insights.

## Steps

1. **Get the URL.** If the user didn't include one, ask for it.

2. **Fetch the transcript and metadata:**
   ```bash
   python3 .claude/skills/video-watch/scripts/fetch_transcript.py "<video-url>"
   ```
   This prints JSON: `{url, method, title, channel, upload_date, duration, transcript}`.

   - Works out of the box for YouTube if `yt-dlp` (recommended) or
     `youtube_transcript_api` is installed.
   - For Skool community posts, Vimeo, Loom, and other yt-dlp-supported
     hosts, `yt-dlp` is tried first automatically.
   - **If the script exits non-zero** (no captions available, private/gated
     video, unsupported platform), don't give up silently: tell the user
     what happened and ask them to paste the transcript or their own notes
     directly into the chat, then continue from step 3 with that text.

3. **Read the transcript and write the summary yourself.** This is the part
   that needs judgment, so do it directly rather than scripting it:
   - A 2-4 sentence overview.
   - **Main Points** — the core content, in the order it builds.
   - **Nuances & Notable Details** — specific caveats, asides, examples, or
     contrarian takes the speaker called out that a generic summary would
     flatten or miss. This is often the most valuable section — look for
     moments where the speaker says something like "most people get this
     wrong" or gives a specific number/threshold/exception.
   - **Actionable Insights** — concrete steps the viewer could actually take,
     phrased as checklist items.

4. **Assemble the note** following
   `.claude/skills/video-watch/references/note_template.md`. Fill in title,
   source URL, platform, creator/channel, today's date, the summary
   sections from step 3, and the full transcript in the collapsible
   section at the bottom.

5. **Save it:**
   ```bash
   python3 .claude/skills/video-watch/scripts/save_note.py "<title>" \
     --vault "/dmac/Documents/knowledge base" --folder "Education" \
     <<< "$FULL_MARKDOWN_CONTENT"
   ```
   - Default vault path is `/dmac/Documents/knowledge base`, default folder
     is `Education`. If the user has previously told you a different vault
     path or wants a different subfolder (e.g. a course-specific folder),
     use that instead.
   - The script auto-avoids overwriting an existing note with the same
     title by appending `(2)`, `(3)`, etc.
   - It prints the final saved path — report that path back to the user.

6. **Multiple videos / playlists:** if given more than one URL, or a
   playlist link, process each video through steps 2-5 separately and
   produce one note per video, unless the user asks for a single combined
   note (e.g. for a multi-part series they want summarized together).

## Notes

- Requires `yt-dlp` for best coverage: `pip install -U yt-dlp` or
  `brew install yt-dlp`. Without it, only plain YouTube URLs work (via
  `youtube_transcript_api`, if installed).
- This skill only has access to whatever filesystem the Claude Code session
  is actually running on. If you're in a sandboxed/remote environment
  without access to the user's real Obsidian vault, save the note locally
  and tell the user where it is so they can move it themselves.
