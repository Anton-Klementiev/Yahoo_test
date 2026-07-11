# NASDAQ-100 Analyst Consensus vs the Index

Tracks the latest analyst consensus for every NASDAQ-100 company and compares each company
against the index as a whole. It exposes the result **both as a REST API and as a website**.
A daily job pulls the data from Yahoo Finance and stores dated snapshots; the API and the page
read those snapshots.

- **Live site:** https://anton-klementiev.github.io/Yahoo_test/
- **Live JSON API:** https://anton-klementiev.github.io/Yahoo_test/api/comparison.json

## What it measures

For each stock, the **consensus** is the analysts' *implied 12-month upside*:

```
implied_upside = (mean analyst price target - current price) / current price
```

The **index** figure is the market-cap-weighted average of that number across the
constituents, and each company's headline number is its **delta** — how far its own implied
upside sits above or below the index's.

## The API

There are two ways to consume the API. Both return the same JSON shape.

### 1. Published (read-only, always on, no server)

Because the data is a read-only daily snapshot, it is published as static JSON on GitHub Pages.
Any system can fetch it — no key, nothing running on anyone's machine:

```
# the whole comparison: index figure + every company's delta
curl https://anton-klementiev.github.io/Yahoo_test/api/comparison.json

# one company
curl https://anton-klementiev.github.io/Yahoo_test/api/company/AAPL.json
```

### 2. Live (running locally, computed on demand, API-key protected)

The FastAPI app serves the same data as live endpoints. Health is public; the data endpoints
require an `X-API-Key` header (set `API_KEY` in your `.env`).

| Method & path              | Auth | Returns                                             |
|----------------------------|------|-----------------------------------------------------|
| `GET /api/health`          | no   | `{"status": "ok"}`                                  |
| `GET /api/comparison`      | yes  | index figure + every company's delta (JSON)         |
| `GET /api/company/{ticker}`| yes  | one company's figures (JSON); 404 if unknown        |

```
curl -H "X-API-Key: YOUR_KEY" http://127.0.0.1:8000/api/comparison
curl -H "X-API-Key: YOUR_KEY" http://127.0.0.1:8000/api/company/AAPL
```

### Response shape

`GET /api/comparison` (and `comparison.json`):

```json
{
  "as_of": "2026-07-11",
  "index_upside": 0.1819,
  "companies": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "price": 210.5,
      "mean_target": 215.0,
      "num_analysts": 34,
      "implied_upside": 0.0214,
      "delta_vs_index": -0.1605,
      "target_last_changed": "2026-07-02",
      "included_in_index": true
    }
  ]
}
```

Fractions are decimals: `0.1819` = +18.19%. `included_in_index` is false for excluded
secondary listings (e.g. `GOOG`). A company with no usable target has `implied_upside` and
`delta_vs_index` of `null`.

## The website

The same numbers as a page with a chart and a sortable table. It is a client of the API —
nothing more.

- **Published:** https://anton-klementiev.github.io/Yahoo_test/ (static, always on)
- **Local:** `uvicorn src.api:app --reload`, then open <http://127.0.0.1:8000/>

## Tech stack

Python 3.11 · yfinance (Yahoo data) · SQLite (`sqlite3`) · FastAPI + uvicorn · Chart.js ·
pytest. No frameworks beyond these; the published site and API are plain static files.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Populate the database (a polite pause between stocks; ~1–2 minutes for the full list):

```
python -m src.ingest
```

## Running locally

```
uvicorn src.api:app --reload
```

Open <http://127.0.0.1:8000/> for the page, <http://127.0.0.1:8000/api/health> to check the
API. The live `/api/comparison` result is cached in memory and rebuilt only when a newer
snapshot date appears, so repeated requests do not recompute it. Run the tests with
`python -m pytest -q`.

## Publishing the site + API (GitHub Pages, free, always on)

1. Refresh the data and regenerate the static files:
   ```
   python -m src.ingest
   python scripts/generate_site.py
   ```
   This writes `docs/index.html`, `docs/api/comparison.json`, and one
   `docs/api/company/<TICKER>.json` per company.

2. Commit and push:
   ```
   git add docs
   git commit -m "refresh published site"
   git push origin master
   ```

3. Enable Pages **once**: repo **Settings → Pages → Build and deployment → Source: Deploy from
   a branch → Branch: `master`, folder: `/docs` → Save**. After ~1 minute the site is live at
   https://anton-klementiev.github.io/Yahoo_test/ and the JSON API under `/api/` beside it.

To update later, repeat steps 1–2; Pages redeploys automatically. Your machine only needs to be
on for that refresh — the published site and API stay up on their own.

## Assumptions and limitations

- **12-month horizon.** Analyst targets are 12-month figures, so the implied upside is a yearly
  expectation, applied consistently to both the stock and the index.
- **Plain market-cap weighting** — an approximation of the official *modified* cap weighting
  (which caps the largest members). Close, free to compute, not identical.
- **Dual-class dedup.** Alphabet lists as both `GOOG` and `GOOGL` and reports the full company
  market cap under each, so `GOOG` is excluded from the index aggregate.
- **"Changed" means the prediction, not the price.** `target_last_changed` moves only when an
  analyst revises the target.
- **Missing coverage is excluded** from the index rather than counted as zero.
- **Published API is a daily snapshot**, not a live query engine: it is a static file refreshed
  when you regenerate and push. That fits data that changes once a day and needs no server.
- **Free, unofficial data source.** Yahoo Finance (via yfinance) can change format or throttle;
  the `DataSource` interface exists so a fallback can be added without touching the rest.

## Maintenance

The constituents list changes only a few times a year (index reconstitution). Update
`data/constituents.csv` by hand when it does.
