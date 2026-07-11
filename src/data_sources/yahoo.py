import logging

import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

from src.models import Quote
from src.data_sources.base import DataSource

logger = logging.getLogger(__name__)


class YahooSource(DataSource):
    """Fetches consensus data from Yahoo Finance via the yfinance library."""
    name = "yahoo"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _download_info(self, ticker: str) -> dict:
        """Ask Yahoo for everything it knows about one ticker. Retried on failure."""
        return yf.Ticker(ticker).info

    def get_quote(self, ticker: str) -> Quote:
        try:
            info = self._download_info(ticker)
        except Exception as error:  # after all retries failed
            logger.warning("Could not fetch %s from Yahoo: %s", ticker, error)
            return Quote(ticker, None, None, None, None, None, None, self.name)

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        quote = Quote(
            ticker=ticker,
            price=price,
            mean_target=info.get("targetMeanPrice"),
            market_cap=info.get("marketCap"),
            num_analysts=info.get("numberOfAnalystOpinions"),
            name=info.get("shortName"),
            currency=info.get("currency"),
            source=self.name,
        )
        if not quote.has_consensus:
            logger.info(
                "No consensus for %s (price=%s, target=%s).",
                ticker, quote.price, quote.mean_target,
            )
        return quote