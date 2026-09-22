#!/usr/bin/env python3
"""Create or update Confluence pages from Markdown."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Local import from sibling script
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from markdown_to_storage import markdown_to_storage  # noqa: E402


def parse_allowed_hosts(raw: str) -> set[str]:
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def validate_base_url(base_url: str, allowed_hosts: set[str], allow_any_host: bool) -> str:
    parsed = urllib.parse.urlparse(base_url.strip())
    if parsed.scheme != "https":
        raise SystemExit("--base-url must use https")
    if not parsed.netloc:
        raise SystemExit("--base-url must include host, e.g. https://wiki.example.com")

    host = (parsed.hostname or "").lower()
    if not allow_any_host and host not in allowed_hosts:
        sorted_hosts = ", ".join(sorted(allowed_hosts))
        raise SystemExit(
            f"Host '{host}' is not allowed. Configure CONFLUENCE_ALLOWED_HOSTS "
            f"or pass --allow-host. Current allowlist: {sorted_hosts}"
        )
    if allow_any_host and allowed_hosts:
        raise SystemExit("Use either --allow-any-host or --allow-host/CONFLUENCE_ALLOWED_HOSTS, not both")

    path = parsed.path.rstrip("/")
    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    return normalized.rstrip("/")


def redact_error_body(body: str) -> str:
    snippet = body[:240]
    # Keep server feedback short and avoid leaking secrets accidentally echoed by proxies.
    for marker in ("token", "authorization", "password", "secret", "apikey", "api_key"):
        snippet = snippet.replace(marker, "***")
        snippet = snippet.replace(marker.upper(), "***")
    return snippet


def request_json(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url=url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    if payload is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code} {method} {url}: {redact_error_body(body)}") from e


def create_page(base_url: str, token: str, space_key: str, ancestor_id: int, title: str, storage: str) -> dict:
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "ancestors": [{"id": str(ancestor_id)}],
        "body": {"storage": {"value": storage, "representation": "storage"}},
    }
    return request_json("POST", f"{base_url}/rest/api/content", token, payload)


def update_page(base_url: str, token: str, page_id: int, title: str, storage: str) -> dict:
    current = request_json("GET", f"{base_url}/rest/api/content/{page_id}?expand=version,space", token)
    next_version = int(current["version"]["number"]) + 1
    payload = {
        "id": str(page_id),
        "type": "page",
        "title": title,
        "space": {"key": current["space"]["key"]},
        "version": {"number": next_version},
        "body": {"storage": {"value": storage, "representation": "storage"}},
    }
    return request_json("PUT", f"{base_url}/rest/api/content/{page_id}", token, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish Markdown to Confluence.")
    parser.add_argument("--base-url", required=True, help="Confluence base URL, e.g. https://wiki.example.com")
    parser.add_argument("--md-file", required=True, help="Input Markdown file")
    parser.add_argument("--title", default="", help="Page title override; defaults to H1 in Markdown")
    parser.add_argument("--token", default="", help="Bearer token (discouraged); defaults to CONFLUENCE_TOKEN env")
    parser.add_argument(
        "--allow-host",
        action="append",
        default=[],
        help="Allowed Confluence hostname; repeatable. Defaults to CONFLUENCE_ALLOWED_HOSTS env",
    )
    parser.add_argument(
        "--allow-any-host",
        action="store_true",
        help="Disable hostname allowlist checks (explicitly unsafe)",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--page-id", type=int, help="Existing page id to update")
    mode.add_argument("--ancestor-id", type=int, help="Parent page id for creating child page")

    parser.add_argument("--space-key", default="", help="Required when creating a child page")
    parser.add_argument("--confirm", action="store_true", help="Required to execute remote Confluence publish")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm:
        raise SystemExit("Refusing to publish without --confirm.")

    env_hosts = parse_allowed_hosts(os.getenv("CONFLUENCE_ALLOWED_HOSTS", ""))
    cli_hosts = {item.strip().lower() for item in args.allow_host if item.strip()}
    allowed_hosts = env_hosts | cli_hosts
    if not args.allow_any_host and not allowed_hosts:
        raise SystemExit(
            "Missing allowlist. Set CONFLUENCE_ALLOWED_HOSTS or pass --allow-host. "
            "Use --allow-any-host only when you fully trust --base-url."
        )

    base_url = validate_base_url(args.base_url, allowed_hosts, args.allow_any_host)

    token = args.token or os.getenv("CONFLUENCE_TOKEN", "")
    if not token:
        raise SystemExit("Missing token: pass --token or set CONFLUENCE_TOKEN")
    if args.token:
        print("Warning: passing --token may leak in shell history; prefer CONFLUENCE_TOKEN env", file=sys.stderr)

    md_file = Path(args.md_file)
    if not md_file.is_file():
        raise SystemExit(f"--md-file not found: {md_file}")
    md_text = md_file.read_text(encoding="utf-8", errors="ignore")
    detected_title, storage = markdown_to_storage(md_text)
    title = args.title.strip() or detected_title

    if args.page_id:
        result = update_page(base_url, token, args.page_id, title, storage)
    else:
        if not args.space_key:
            raise SystemExit("--space-key is required when using --ancestor-id")
        result = create_page(base_url, token, args.space_key, args.ancestor_id, title, storage)

    webui = result.get("_links", {}).get("webui", "")
    print(f"id={result.get('id')}")
    print(f"title={result.get('title')}")
    if "version" in result:
        print(f"version={result['version'].get('number')}")
    if webui:
        print(f"url={base_url}{webui}")


if __name__ == "__main__":
    main()
