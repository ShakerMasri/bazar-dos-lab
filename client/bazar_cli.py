"""Run on the host OS: python client/bazar_cli.py search 'distributed systems'."""
import argparse
import json
import sys
from urllib.parse import quote

import requests


def main():
    parser = argparse.ArgumentParser(description="Bazar.com command-line client")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Frontend base URL")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("search").add_argument("topic")
    actions.add_parser("info").add_argument("item_id", type=int)
    actions.add_parser("purchase").add_argument("item_id", type=int)
    args = parser.parse_args()

    base = args.url.rstrip("/")
    if args.action == "search":
        path = "/search/" + quote(args.topic, safe="")
        method = "GET"
    else:
        path = f"/{args.action}/{args.item_id}"
        method = "POST" if args.action == "purchase" else "GET"

    try:
        response = requests.request(method, base + path, timeout=10)
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"Network or response error: {exc}", file=sys.stderr)
        return 1

    print(f"{method} {path} -> HTTP {response.status_code}")
    if args.action == "search" and isinstance(payload, list):
        for entry in payload:
            print(f"  #{entry['id']}: {entry['title']}")
        if not payload:
            print("  No books found")
    else:
        print(json.dumps(payload, indent=2))
    return 0 if response.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
