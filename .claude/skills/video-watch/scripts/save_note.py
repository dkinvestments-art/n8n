#!/usr/bin/env python3
"""Save a finished markdown note into the Obsidian vault.

Reads the full markdown content from stdin (frontmatter + summary +
transcript, already assembled by the caller) and writes it to
<vault>/<folder>/<title>.md, avoiding collisions with existing notes.

Prints the final saved path to stdout on success.
"""
import argparse
import re
import sys
from pathlib import Path


def slugify_title(title):
    title = title.strip()
    title = re.sub(r"[\\/:*?\"<>|]", "-", title)
    title = re.sub(r"\s+", " ", title)
    return title[:150].strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", help="Video title, used as the note filename")
    parser.add_argument(
        "--vault",
        default="/dmac/Documents/knowledge base",
        help="Path to the Obsidian vault root (default: %(default)s)",
    )
    parser.add_argument(
        "--folder",
        default="Education",
        help="Subfolder inside the vault to save into (default: %(default)s)",
    )
    args = parser.parse_args()

    content = sys.stdin.read()
    if not content.strip():
        print("No content received on stdin", file=sys.stderr)
        sys.exit(1)

    target_dir = Path(args.vault) / args.folder
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = slugify_title(args.title) or "Untitled Video Note"
    candidate = target_dir / f"{base_name}.md"
    counter = 2
    while candidate.exists():
        candidate = target_dir / f"{base_name} ({counter}).md"
        counter += 1

    candidate.write_text(content, encoding="utf-8")
    print(str(candidate))


if __name__ == "__main__":
    main()
