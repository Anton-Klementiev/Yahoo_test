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


def _load_comparison() -> dict:
    """Open the database, build the comparison, and always close the connection."""
    connection = get_connection()
    try:
        return build_comparison(connection)
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