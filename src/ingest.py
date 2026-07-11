import logging
import time
from datetime import date
from pathlib import Path

from src.constituents import get_constituents
from src.data_sources.yahoo import YahooSource
from src.database import init_db, get_connection, save_snapshot, get_latest_snapshot

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = PROJECT_ROOT / "logs" / "ingest.log"
THROTTLE_SECONDS = 0.7   # brief pause between stocks, to be polite to the data source


def _configure_logging() -> None:
    """Send logs to both the console and a file, so unattended runs leave a record."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _target_changed(old, new, tolerance: float = 0.01) -> bool:
    """True if the analyst target moved meaningfully, or appeared/disappeared."""
    if old is None and new is None:
        return False
    if old is None or new is None:
        return True
    return abs(old - new) > tolerance   # ignore sub-cent float noise


def run_ingestion(limit: int | None = None) -> None:
    init_db()
    tickers = get_constituents()
    if limit:                      # used only for quick testing
        tickers = tickers[:limit]

    source = YahooSource()
    today = date.today().isoformat()
    with_consensus = without_consensus = failed = changes = 0

    connection = get_connection()
    try:
        for position, ticker in enumerate(tickers, start=1):
            quote = source.get_quote(ticker)

            if quote.price is None and quote.mean_target is None:
                failed += 1
            elif not quote.has_consensus:
                without_consensus += 1
            else:
                with_consensus += 1

            prior = get_latest_snapshot(connection, ticker)
            prior_target = prior["mean_target"] if prior else None

            if prior is None:
                target_last_changed = today                         # first time we've seen it
            elif _target_changed(prior_target, quote.mean_target):
                target_last_changed = today                         # analyst target moved
                changes += 1
            else:
                target_last_changed = prior["target_last_changed"] or today  # unchanged: carry the date

            save_snapshot(connection, quote, observed_on=today,
                          target_last_changed=target_last_changed)
            connection.commit()     # persist this stock immediately (resilience)

            logger.info("[%d/%d] %s done.", position, len(tickers), ticker)
            time.sleep(THROTTLE_SECONDS)
    finally:
        connection.close()

    logger.info(
        "Ingestion complete for %s: %d with consensus, %d without, %d failed, %d target changes.",
        today, with_consensus, without_consensus, failed, changes,
    )


def main() -> None:
    _configure_logging()
    logger.info("Starting daily ingestion...")
    try:
        run_ingestion()
    except Exception:
        logger.exception("Ingestion failed with an unexpected error.")
        raise   # non-zero exit so the scheduler knows it failed


if __name__ == "__main__":
    main()