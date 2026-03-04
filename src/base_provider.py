from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class StockDataProvider(ABC):
    """
    Abstract interface for fetching market data.
    Allows for multiple providers (FMP, QUICK, etc.)
    """

    @abstractmethod
    def get_stock_screener(self, market_cap_min: float, market: str) -> List[Dict[str, Any]]:
        """Get list of stocks filtered by market cap."""
        pass

    @abstractmethod
    def get_quote(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get real-time/delayed quotes for a list of symbols."""
        pass

    @abstractmethod
    def get_historical_daily(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get historical daily prices for a symbol."""
        pass

    @abstractmethod
    def get_earnings_calendar(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get earnings events for a date range."""
        pass

    @abstractmethod
    def get_analyst_estimates(self, symbol: str) -> List[Dict[str, Any]]:
        """Get analyst estimates and revisions."""
        pass

    @abstractmethod
    def get_news(self, tickers: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent news for specific tickers."""
        pass
    
    @abstractmethod
    def get_general_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get general market news."""
        pass
