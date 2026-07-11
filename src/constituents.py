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

CONSTITUENTS_PATH = Path("data") / "constituents.csv"


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