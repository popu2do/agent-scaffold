#!/usr/bin/env python3
"""Create or update a GitLab wiki page from Markdown."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def run_git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def update_home(home_file: Path, page_title: str, slug: str) -> None:
    link_line = f"- [{page_title}]({slug})"
    if home_file.exists():
        text = home_file.read_text(encoding="utf-8")
        if link_line in text:
            return
    else:
        text = "# Wiki\n\n## 更新说明\n"

    if "## 更新说明" not in text:
        text = text.rstrip() + "\n\n## 更新说明\n"

    if not text.endswith("\n"):
        text += "\n"
    text += f"{link_line}\n"
    home_file.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish Markdown to GitLab wiki.")
    parser.add_argument("--wiki-remote", required=True, help="GitLab wiki git remote, e.g. git@host:group/proj.wiki.git")
    parser.add_argument("--md-file", required=True, help="Markdown file to publish")
    parser.add_argument("--slug", required=True, help="Wiki slug without .md, e.g. release-notes-260706a")
    parser.add_argument("--title", required=True, help="Page title used for optional home link")
    parser.add_argument("--commit-message", default="docs: update wiki page", help="Commit message")
    parser.add_argument("--update-home", action="store_true", help="Append page link to home.md")
    parser.add_argument("--confirm", action="store_true", help="Required to execute remote wiki publish")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    md_file = Path(args.md_file)
    if not md_file.is_file():
        raise SystemExit(f"--md-file not found: {md_file}")
    if not args.confirm:
        raise SystemExit("Refusing to publish without --confirm.")

    temp_dir = Path(tempfile.mkdtemp(prefix="gitlab-wiki-"))
    try:
        run_git(["clone", args.wiki_remote, str(temp_dir)])
        target = temp_dir / f"{args.slug}.md"
        target.write_text(md_file.read_text(encoding="utf-8"), encoding="utf-8")

        if args.update_home:
            update_home(temp_dir / "home.md", args.title, args.slug)

        run_git(["add", "."], cwd=temp_dir)
        status = run_git(["status", "--short"], cwd=temp_dir)
        if not status:
            print("No wiki changes to publish.")
            return

        run_git(["commit", "-m", args.commit_message], cwd=temp_dir)
        run_git(["push", "origin", "master"], cwd=temp_dir)
        print(f"page={args.slug}")
        print(f"updated_home={str(args.update_home).lower()}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
