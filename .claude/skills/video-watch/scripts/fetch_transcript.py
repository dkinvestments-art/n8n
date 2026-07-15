#!/usr/bin/env python3
"""Fetch a video's transcript + metadata and print them as JSON.

Tries, in order:
  1. yt-dlp (covers YouTube, Vimeo, and hundreds of other sites, including
     many embeds found on community platforms like Skool when the video is
     actually hosted on YouTube/Vimeo/Wistia under the hood).
  2. youtube_transcript_api, as a lighter-weight fallback for plain YouTube
     URLs when yt-dlp is unavailable or has no subtitle track.

If neither works, exits with a non-zero status and an error message on
stderr describing what happened, so the caller can fall back to asking the
user for a manually-copied transcript.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def have_binary(name):
    return run(["which", name]).returncode == 0


def vtt_to_text(vtt_path):
    """Collapse a WebVTT caption file into deduplicated plain-text lines."""
    raw = Path(vtt_path).read_text(encoding="utf-8", errors="ignore")
    lines = []
    seen_last = None
    for line in raw.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT":
            continue
        if "-->" in line:
            continue
        if re.match(r"^\d+$", line):
            continue
        # Strip inline VTT tags like <00:00:01.234><c> word</c>
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line:
            continue
        # Auto-captions repeat the previous line as context; skip exact dupes.
        if line == seen_last:
            continue
        lines.append(line)
        seen_last = line
    return "\n".join(lines)


def fetch_via_ytdlp(url, workdir):
    if not have_binary("yt-dlp"):
        return None, "yt-dlp is not installed"

    info = run(["yt-dlp", "--dump-json", "--no-warnings", "--skip-download", url])
    if info.returncode != 0:
        return None, f"yt-dlp could not read video info: {info.stderr.strip()[-500:]}"

    meta = json.loads(info.stdout.splitlines()[-1])

    sub_result = run([
        "yt-dlp", "--skip-download", "--no-warnings",
        "--write-auto-sub", "--write-sub",
        "--sub-lang", "en.*,en",
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        "-o", str(Path(workdir) / "%(id)s.%(ext)s"),
        url,
    ])

    vtt_files = sorted(Path(workdir).glob("*.vtt"))
    if not vtt_files:
        return {
            "title": meta.get("title"),
            "channel": meta.get("uploader") or meta.get("channel"),
            "upload_date": meta.get("upload_date"),
            "duration": meta.get("duration"),
            "transcript": None,
        }, f"yt-dlp found the video but no subtitle track ({sub_result.stderr.strip()[-300:]})"

    transcript = vtt_to_text(vtt_files[0])
    return {
        "title": meta.get("title"),
        "channel": meta.get("uploader") or meta.get("channel"),
        "upload_date": meta.get("upload_date"),
        "duration": meta.get("duration"),
        "transcript": transcript,
    }, None


def fetch_via_youtube_transcript_api(url):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None, "youtube_transcript_api is not installed"

    match = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url)
    if not match:
        return None, "could not extract a YouTube video ID from the URL"
    video_id = match.group(1)

    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
    except Exception as exc:  # noqa: BLE001 - surfacing any transcript-api error is intended here
        return None, str(exc)

    transcript = "\n".join(seg["text"].strip() for seg in segments if seg["text"].strip())
    return {"title": None, "channel": None, "upload_date": None, "duration": None, "transcript": transcript}, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Video URL (YouTube, Skool, Vimeo, etc.)")
    args = parser.parse_args()

    errors = []
    with tempfile.TemporaryDirectory() as workdir:
        result, err = fetch_via_ytdlp(args.url, workdir)
        if err:
            errors.append(f"yt-dlp: {err}")
        if result and result.get("transcript"):
            print(json.dumps({"url": args.url, "method": "yt-dlp", **result}))
            return

    result, err = fetch_via_youtube_transcript_api(args.url)
    if err:
        errors.append(f"youtube_transcript_api: {err}")
    if result and result.get("transcript"):
        print(json.dumps({"url": args.url, "method": "youtube_transcript_api", **result}))
        return

    print(
        "Could not automatically fetch a transcript.\n" + "\n".join(errors) +
        "\n\nAsk the user to paste the transcript manually, or check that yt-dlp "
        "(`pip install -U yt-dlp` or `brew install yt-dlp`) is installed.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
