#!/usr/bin/env python3
"""Convert a Markdown file into Confluence storage HTML (basic subset)."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def fmt_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


def markdown_to_storage(md: str) -> tuple[str, str]:
    lines = md.splitlines()
    title = ""
    parts: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1 and not title:
                title = text
            else:
                parts.append(f"<h{level}>{fmt_inline(text)}</h{level}>")
            i += 1
            continue

        if re.match(r"^-\s+", line):
            items = []
            while i < len(lines) and re.match(r"^-\s+", lines[i]):
                items.append(re.sub(r"^-\s+", "", lines[i]).strip())
                i += 1
            parts.append("<ul>" + "".join(f"<li>{fmt_inline(it)}</li>" for it in items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i]).strip())
                i += 1
            parts.append("<ol>" + "".join(f"<li>{fmt_inline(it)}</li>" for it in items) + "</ol>")
            continue

        para = [line.strip()]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if not nxt.strip() or re.match(r"^(#{1,6})\s+", nxt) or re.match(r"^-\s+", nxt) or re.match(r"^\d+\.\s+", nxt):
                break
            para.append(nxt.strip())
            i += 1
        parts.append(f"<p>{fmt_inline(' '.join(para))}</p>")

    if not title:
        title = "Untitled"

    return title, "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown to Confluence storage HTML.")
    parser.add_argument("--md-file", required=True, help="Input Markdown file path.")
    parser.add_argument("--output", required=True, help="Output HTML file path.")
    parser.add_argument("--title-output", default="", help="Optional title output text file.")
    args = parser.parse_args()

    md_text = Path(args.md_file).read_text(encoding="utf-8", errors="ignore")
    title, storage = markdown_to_storage(md_text)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(storage, encoding="utf-8")

    if args.title_output:
        Path(args.title_output).write_text(title, encoding="utf-8")

    print(f"Title: {title}")
    print(f"Storage written: {out}")


if __name__ == "__main__":
    main()
