import logging

logger = logging.getLogger(__name__)

# Dual-class companies report the FULL company market cap under each ticker,
# so we drop the secondary listing to avoid counting the company twice.
SECONDARY_LISTINGS = {"GOOG"}   # keep GOOGL, drop GOOG


def get_latest_snapshots(connection):
    """Return the most recent snapshot row for every ticker."""
    cursor = connection.execute(
        """
        SELECT s.*
        FROM snapshots AS s
        JOIN (
            SELECT ticker, MAX(observed_on) AS latest
            FROM snapshots
            GROUP BY ticker
        ) AS newest
          ON s.ticker = newest.ticker
         AND s.observed_on = newest.latest
        """
    )
    return cursor.fetchall()


def compute_index_upside(snapshots):
    """Market-cap-weighted average implied upside across eligible stocks.

    Returns (index_upside, list_of_eligible_rows). A stock is eligible only if
    it is not a secondary listing and has both an implied upside and a market cap.
    """
    eligible = [
        row for row in snapshots
        if row["ticker"] not in SECONDARY_LISTINGS
        and row["implied_upside"] is not None
        and row["market_cap"]
    ]
    total_cap = sum(row["market_cap"] for row in eligible)
    if total_cap == 0:
        return None, []
    weighted = sum(row["implied_upside"] * row["market_cap"] for row in eligible) / total_cap
    return weighted, eligible


def build_comparison(connection):
    """Assemble the full picture: the index number plus each stock's delta versus it."""
    snapshots = get_latest_snapshots(connection)
    index_upside, eligible = compute_index_upside(snapshots)
    eligible_tickers = {row["ticker"] for row in eligible}

    companies = []
    for row in snapshots:
        upside = row["implied_upside"]
        if upside is not None and index_upside is not None:
            delta = upside - index_upside
        else:
            delta = None
        companies.append({
            "ticker": row["ticker"],
            "price": row["price"],
            "mean_target": row["mean_target"],
            "num_analysts": row["num_analysts"],
            "implied_upside": upside,
            "delta_vs_index": delta,
            "target_last_changed": row["target_last_changed"],
            "included_in_index": row["ticker"] in eligible_tickers,
        })

    # Most bullish-versus-index first; stocks with no delta sink to the bottom.
    companies.sort(key=lambda c: (c["delta_vs_index"] is None, -(c["delta_vs_index"] or 0)))

    as_of = max((row["observed_on"] for row in snapshots), default=None)
    return {"as_of": as_of, "index_upside": index_upside, "companies": companies}