"""Generate the static site + read-only JSON API into docs/ for GitHub Pages.

Because the data is a read-only daily snapshot, we do not need a running server to
serve it to other people. This script renders the current data to static files that
GitHub Pages hosts for free, always-on, with nothing of yours turned on:

    docs/index.html                     the web page (fetches the static JSON below)
    docs/api/comparison.json            the whole comparison (mirrors GET /api/comparison)
    docs/api/company/<TICKER>.json      one company each (mirrors GET /api/company/{ticker})

Run it locally after ingestion, then commit and push docs/ to publish:

    python -m src.ingest
    python scripts/generate_site.py
    git add docs && git commit -m "refresh published site" && git push
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.aggregation import build_comparison  # noqa: E402
from src.database import get_connection  # noqa: E402

DOCS = PROJECT_ROOT / "docs"
WEB = PROJECT_ROOT / "web"

# The live page calls the authenticated API; the static page fetches the JSON file
# published beside it. This is the only difference between the two.
_LIVE_FETCH = 'await fetch("/api/comparison", { headers: { "X-API-Key": API_KEY } })'
_STATIC_FETCH = 'await fetch("./api/comparison.json")'


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(docs_dir: Path | None = None) -> None:
    docs = docs_dir or DOCS

    connection = get_connection()
    try:
        data = build_comparison(connection)
    finally:
        connection.close()

    # Whole-comparison endpoint.
    _write_json(docs / "api" / "comparison.json", data)

    # Per-company endpoints, mirroring GET /api/company/{ticker}.
    for company in data["companies"]:
        payload = {
            "as_of": data["as_of"],
            "index_upside": data["index_upside"],
            "company": company,
        }
        _write_json(docs / "api" / "company" / f"{company['ticker']}.json", payload)

    # Static page: the live page, repointed at the published JSON (no API key needed).
    html = (WEB / "index.html").read_text(encoding="utf-8")
    if _LIVE_FETCH not in html:
        raise SystemExit(
            "Could not find the API fetch call in web/index.html; "
            "update _LIVE_FETCH in scripts/generate_site.py to match."
        )
    html = html.replace(_LIVE_FETCH, _STATIC_FETCH)
    (docs / "index.html").write_text(html, encoding="utf-8")

    # Tell GitHub Pages not to run Jekyll over these files.
    (docs / ".nojekyll").write_text("", encoding="utf-8")

    print(
        f"Generated {docs}: index.html + api/comparison.json "
        f"+ {len(data['companies'])} company files (as_of {data['as_of']})."
    )


if __name__ == "__main__":
    main()
