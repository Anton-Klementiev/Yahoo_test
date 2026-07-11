import math

from src.aggregation import compute_index_upside


def make(ticker, upside, cap):
    """A minimal stand-in for a database row (dict indexing works the same way)."""
    return {"ticker": ticker, "implied_upside": upside, "market_cap": cap}


def test_weighting_is_market_cap_weighted():
    # (0.10*100 + 0.20*300) / 400 = 70/400 = 0.175
    rows = [make("A", 0.10, 100), make("B", 0.20, 300)]
    index_upside, eligible = compute_index_upside(rows)
    assert math.isclose(index_upside, 0.175, rel_tol=1e-9)
    assert len(eligible) == 2


def test_secondary_listing_is_excluded():
    # GOOG must be dropped so Alphabet is not counted twice.
    rows = [make("GOOGL", 0.10, 100), make("GOOG", 0.99, 100), make("B", 0.20, 300)]
    _, eligible = compute_index_upside(rows)
    tickers = {row["ticker"] for row in eligible}
    assert "GOOG" not in tickers
    assert "GOOGL" in tickers


def test_missing_data_is_ignored():
    # Only A has both an upside and a market cap, so the index equals A's upside.
    rows = [make("A", 0.10, 100), make("B", None, 300), make("C", 0.20, None)]
    index_upside, eligible = compute_index_upside(rows)
    assert math.isclose(index_upside, 0.10, rel_tol=1e-9)
    assert len(eligible) == 1