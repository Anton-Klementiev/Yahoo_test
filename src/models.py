from dataclasses import dataclass
from typing import Optional


@dataclass
class Quote:
    """One snapshot of consensus data for a single stock."""
    ticker: str                      # the stock symbol, e.g. "AAPL"
    price: Optional[float]           # current share price
    mean_target: Optional[float]     # average analyst 12-month price target
    market_cap: Optional[float]      # total market value (used later for weighting)
    num_analysts: Optional[int]      # how many analysts contributed
    name: Optional[str]              # human-readable company name
    currency: Optional[str]          # e.g. "USD"
    source: str                      # which data source produced this

    @property
    def implied_upside(self) -> Optional[float]:
        """(target - price) / price. None if we lack the inputs."""
        if self.price and self.mean_target and self.price > 0:
            return (self.mean_target - self.price) / self.price
        return None

    @property
    def has_consensus(self) -> bool:
        """True only when we could actually compute an upside."""
        return self.implied_upside is not None