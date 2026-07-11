import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse

from src.database import get_connection
from src.aggregation import build_comparison
from src.auth import require_api_key
from src.config import API_KEY

logger = logging.getLogger(__name__)

app = FastAPI(title="NASDAQ-100 Consensus vs Index")

WEB_DIR = Path(__file__).resolve().parents[1] / "web"


# In-memory cache of the built comparison. The underlying data changes only once a day
# (after ingestion writes a new dated snapshot), so we rebuild the comparison only when a
# newer snapshot date appears — instead of recomputing it from the database on every
# request. Keyed by the latest observed_on date; a cheap MAX() query decides freshness.
_cache: dict = {"as_of": None, "data": None}


def _latest_observed_on(connection) -> str | None:
    """The most recent snapshot date, or None if there are no snapshots yet."""
    row = connection.execute("SELECT MAX(observed_on) AS latest FROM snapshots").fetchone()
    return row["latest"] if row else None


def _load_comparison() -> dict:
    """Return the comparison, rebuilding it only when new data has arrived.

    Opens the database, checks the latest snapshot date cheaply, and reuses the cached
    result if nothing has changed. The expensive build_comparison runs only when the
    latest date differs from what is cached. The connection is always closed.
    """
    connection = get_connection()
    try:
        latest = _latest_observed_on(connection)
        if _cache["data"] is not None and _cache["as_of"] == latest:
            return _cache["data"]
        data = build_comparison(connection)
        _cache["as_of"] = latest
        _cache["data"] = data
        return data
    finally:
        connection.close()


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the web page with the API key injected at load time."""
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    return html.replace("__API_KEY__", API_KEY)


@app.get("/api/health")
def health() -> dict:
    """A trivial endpoint to confirm the server is running."""
    return {"status": "ok"}


@app.get("/api/comparison", dependencies=[Depends(require_api_key)])
def comparison() -> dict:
    """The index number plus every company's delta versus it."""
    return _load_comparison()


@app.get("/api/company/{ticker}", dependencies=[Depends(require_api_key)])
def company(ticker: str) -> dict:
    """The latest figures for a single company."""
    ticker = ticker.upper()
    data = _load_comparison()
    for entry in data["companies"]:
        if entry["ticker"] == ticker:
            return {
                "as_of": data["as_of"],
                "index_upside": data["index_upside"],
                "company": entry,
            }
    raise HTTPException(status_code=404, detail=f"{ticker} not found")