#!/usr/bin/env python3
"""Collect a stable preflight summary for worktree-based tasks."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run_git(repo: Path, *args: str) -> tuple[int, str, str]:
    process = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return process.returncode, process.stdout.strip(), process.stderr.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository path")
    parser.add_argument("--base-branch", default="", help="Branch to branch off from")
    parser.add_argument("--integration-target", default="", help="Final merge target")
    parser.add_argument("--remote-scope", default="local-only", help="Allowed remote scope")
    parser.add_argument(
        "--worktree-root",
        default="",
        help=(
            "Worktree root path. If omitted, defaults to "
            "<repo-parent>/<repo-name>-worktrees"
        ),
    )
    parser.add_argument("--task-slug", default="", help="Task slug for suggested path")
    parser.add_argument("--branch-name", default="", help="Branch name for the worktree")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    return parser.parse_args()


def resolve_worktree_root(repo_root: Path, args: argparse.Namespace) -> Path:
    if args.worktree_root:
        raw = Path(args.worktree_root)
        return (repo_root / raw).resolve() if not raw.is_absolute() else raw.resolve()
    return (repo_root.parent / f"{repo_root.name}-worktrees").resolve()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()

    code, root_out, root_err = run_git(repo, "rev-parse", "--show-toplevel")
    if code != 0:
        raise SystemExit(root_err or "Not a git repository")
    repo_root = Path(root_out)

    current_branch = run_git(repo_root, "branch", "--show-current")[1]
    baseline_commit = run_git(repo_root, "rev-parse", "--short", "HEAD")[1]
    status_out = run_git(repo_root, "status", "--short")[1]
    worktree_list = run_git(repo_root, "worktree", "list")[1]
    worktree_root = resolve_worktree_root(repo_root, args)

    suggested_path = ""
    if args.task_slug:
        suggested = (worktree_root / args.task_slug).resolve()
        suggested_path = str(suggested)

    risks: list[str] = []
    if status_out:
        risks.append("主工作区存在未提交修改")
    if args.integration_target and args.integration_target.startswith("origin/") and args.remote_scope == "local-only":
        risks.append("集成目标指向远程分支，但 remote_scope 仍是 local-only")
    if args.integration_target in {"local-only", "local_only"}:
        risks.append("integration_target 不应填写 local-only；请改为填写 remote_scope")
    if not args.base_branch:
        risks.append("未明确 base_branch")
    if not args.integration_target:
        risks.append("未明确 integration_target（允许阶段性 <unset>，收口前必须确认）")

    payload = {
        "repo_root": str(repo_root),
        "current_branch": current_branch,
        "baseline_commit": baseline_commit,
        "base_branch": args.base_branch or "<unset>",
        "integration_target": args.integration_target or "<unset>",
        "remote_scope": args.remote_scope,
        "worktree_root": str(worktree_root),
        "branch_name": args.branch_name or "<unset>",
        "suggested_worktree": suggested_path or "<unset>",
        "workspace_dirty": bool(status_out),
        "status_lines": [line for line in status_out.splitlines() if line],
        "worktrees": [line for line in worktree_list.splitlines() if line],
        "risks": risks or ["无明显阻塞，继续人工确认即可"],
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("前置完成")
    print(f"- repo_root: {payload['repo_root']}")
    print(f"- current_branch: {payload['current_branch']}")
    print(f"- baseline_commit: {payload['baseline_commit']}")
    print(f"- base_branch: {payload['base_branch']}")
    print(f"- integration_target: {payload['integration_target']}")
    print(f"- remote_scope: {payload['remote_scope']}")
    print(f"- worktree_root: {payload['worktree_root']}")
    print(f"- branch_name: {payload['branch_name']}")
    print(f"- suggested_worktree: {payload['suggested_worktree']}")
    print(f"- workspace_dirty: {'yes' if payload['workspace_dirty'] else 'no'}")
    print("- risks:")
    for item in payload["risks"]:
        print(f"  - {item}")
    if payload["status_lines"]:
        print("- status:")
        for line in payload["status_lines"]:
            print(f"  - {line}")
    if payload["worktrees"]:
        print("- worktrees:")
        for line in payload["worktrees"]:
            print(f"  - {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
