"""Provides the list of NASDAQ-100 member tickers.

Index membership changes only a few times per year (at the annual
reconstitution), so we keep a version-controlled list in data/constituents.csv
rather than scraping it live on every run. This is more reliable and
non-disruptive: there is no fragile web request that can silently break the
daily job. When the index reconstitutes, update the CSV file by hand.
"""
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Resolve relative to the project root (the folder above src/), NOT the current working
# directory — otherwise the load breaks whenever the app is launched from anywhere else.
# This matches how src/database.py already resolves its DB path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONSTITUENTS_PATH = PROJECT_ROOT / "data" / "constituents.csv"


def get_constituents() -> list[str]:
    """Return the NASDAQ-100 member tickers from the bundled CSV file."""
    if not CONSTITUENTS_PATH.exists():
        raise FileNotFoundError(
            f"Constituents file not found at {CONSTITUENTS_PATH}. "
            "It should be committed as part of the project."
        )
    column = pd.read_csv(CONSTITUENTS_PATH)["ticker"]
    tickers = column.astype(str).str.strip().str.upper().tolist()
    tickers = sorted({t for t in tickers if t})  # de-duplicate and drop blanks
    logger.info("Loaded %d constituents from %s.", len(tickers), CONSTITUENTS_PATH)
    return tickers