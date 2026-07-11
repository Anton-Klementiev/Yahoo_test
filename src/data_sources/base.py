from abc import ABC, abstractmethod

from src.models import Quote

class DataSource(ABC):
    """The contract every data source must fulfill."""
    name: str = "base"

    @abstractmethod
    def get_quote(self, ticker: str) -> Quote:
        """Return a Quote for one ticker. Must never raise; on failure,
        return a Quote with empty fields so one bad ticker can't stop the run."""
        raise NotImplementedError