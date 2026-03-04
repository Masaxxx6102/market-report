import requests
import urllib3
import yfinance as yf
from typing import List, Dict, Any, Optional
from .base_provider import StockDataProvider
from .logger_setup import logger

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class YFinanceProvider(StockDataProvider):
    """
    Implementation of StockDataProvider using yfinance library.
    Ideal for Japanese stocks and indices when QUICK is not available.
    """

    def __init__(self):
        pass

    def get_stock_screener(self, market_cap_min: float = None, market: str = "US") -> List[Dict[str, Any]]:
        """
        yfinance doesn't have a direct screening API like FMP.
        This is a placeholder or should be handled by another provider for discovery.
        """
        logger.warning("yfinance does not support stock screening. Returning empty list.")
        return []

    def get_quote(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch quotes for symbols using yfinance."""
        if not symbols:
            return []
        
        results = []
        for symbol in symbols:
            # Handle TOPIX mapping
            search_symbol = symbol
            if symbol.upper() == "TOPIX":
                search_symbol = "^TPX"
            
            try:
                ticker = yf.Ticker(search_symbol)
                # Use history instead of info for more reliable price fetching
                hist = ticker.history(period="2d")
                
                if hist.empty:
                    logger.warning(f"yfinance returned no history for {search_symbol}")
                    continue
                
                price = hist["Close"].iloc[-1]
                prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else price
                
                # Get descriptive name if possible (info is too slow, but we can use ticker string)
                name = symbol
                
                results.append({
                    "symbol": symbol, 
                    "name": name, 
                    "price": float(price),
                    "change": float(price - prev_close),
                    "changesPercentage": float((price - prev_close) / prev_close * 100) if prev_close else 0.0,
                    "previousClose": float(prev_close),
                    "marketCap": 0 
                })
            except Exception as e:
                logger.error(f"yfinance error fetching quote for {symbol}: {e}")
                
        return results

    def get_historical_daily(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get historical data from yfinance."""
        # Handle TOPIX mapping
        search_symbol = symbol
        if symbol.upper() == "TOPIX":
            search_symbol = "^TPX"
            
        try:
            ticker = yf.Ticker(search_symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            records = []
            for date, row in hist.iterrows():
                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "close": row["Close"],
                    "high": row["High"],
                    "low": row["Low"],
                    "open": row["Open"],
                    "volume": row["Volume"]
                })
            return records
        except Exception as e:
            logger.error(f"yfinance error fetching history for {symbol}: {e}")
            return []

    def get_earnings_calendar(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        # yfinance earnings calendar is tricky for large batches
        return []

    def get_analyst_estimates(self, symbol: str) -> List[Dict[str, Any]]:
        return []

    def get_news(self, tickers: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        # yfinance provides some news but format varies
        return []

    def get_general_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        return []
