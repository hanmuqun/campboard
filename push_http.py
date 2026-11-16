"""Post the snapshot to the site's own ingest endpoint.

This is the CI-friendly replacement for push_d1.py: no wrangler, no Cloudflare
API token, no npm install - just one HTTPS POST with a shared key.

    python push_http.py
    python push_http.py --dry-run
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DEFAULT_URL = "https://campboard.wwangjunling7.workers.dev/api/ingest"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("CAMPBOARD_INGEST_URL", DEFAULT_URL))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    snapshot = json.loads((DATA / "snapshot.json").read_text(encoding="utf-8"))
    changes_path = DATA / "changes.json"
    changes = json.loads(changes_path.read_text(encoding="utf-8")) if changes_path.exists() else []

    payload = {
        "generated": snapshot["generated"],
        "campgrounds": snapshot["campgrounds"],
        "changes": changes,
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    print(f"payload: {len(snapshot['campgrounds'])} campgrounds, {len(changes)} changes, {len(body)} bytes")

    if args.dry_run:
        print("dry run, not posting")
        return

    key = os.environ.get("INGEST_KEY")
    if not key:
        sys.exit("INGEST_KEY is not set")

    req = urllib.request.Request(
        args.url,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-ingest-key": key,
            # Cloudflare blocks python-urllib's default signature with error 1010.
            "user-agent": "campboard-fetcher/1.0 (+https://campboard.wwangjunling7.workers.dev)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
            print(f"{r.status} {text[:300]}")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001 - network failures should fail the job loudly
        print(f"POST failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
