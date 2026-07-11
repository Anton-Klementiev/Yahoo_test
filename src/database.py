import logging
import sqlite3
from pathlib import Path

from src.models import Quote

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "consensus.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    ticker              TEXT NOT NULL,
    observed_on         TEXT NOT NULL,   -- date of this observation, "YYYY-MM-DD"
    price               REAL,
    mean_target         REAL,
    market_cap          REAL,
    num_analysts        INTEGER,
    implied_upside      REAL,
    source              TEXT,
    target_last_changed TEXT,            -- date the analyst target last moved
    PRIMARY KEY (ticker, observed_on)
);
"""


def get_connection() -> sqlite3.Connection:
    """Open a connection to the database, creating the data/ folder if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row   # lets us read columns by name, not position
    return connection


def init_db() -> None:
    """Create the table if it does not already exist. Safe to run repeatedly."""
    with get_connection() as connection:
        connection.executescript(SCHEMA)
    logger.info("Database ready at %s", DB_PATH)


def save_snapshot(
    connection: sqlite3.Connection,
    quote: Quote,
    observed_on: str,
    target_last_changed: str,
) -> None:
    """Insert (or overwrite) one ticker's snapshot for a given date."""
    connection.execute(
        """
        INSERT OR REPLACE INTO snapshots
            (ticker, observed_on, price, mean_target, market_cap,
             num_analysts, implied_upside, source, target_last_changed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            quote.ticker, observed_on, quote.price, quote.mean_target,
            quote.market_cap, quote.num_analysts, quote.implied_upside,
            quote.source, target_last_changed,
        ),
    )


def get_latest_snapshot(connection: sqlite3.Connection, ticker: str) -> sqlite3.Row | None:
    """Return the most recent stored row for a ticker, or None if there is none."""
    cursor = connection.execute(
        "SELECT * FROM snapshots WHERE ticker = ? ORDER BY observed_on DESC LIMIT 1",
        (ticker,),
    )
    return cursor.fetchone()