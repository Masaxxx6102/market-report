import requests
import tenacity
from typing import List, Dict, Any
from .base_provider import StockDataProvider
from .logger_setup import logger

class FMPPaymentRequiredError(Exception):
    """Custom exception for 402 errors to skip retries."""
    pass

class FMPProvider(StockDataProvider):
    """
    Implementation of StockDataProvider using Financial Modeling Prep (FMP) API.
    """
    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3), 
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10)
    )
    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["apikey"] = self.api_key
        
        try:
            response = requests.get(url, params=params, verify=False)
            if response.status_code == 402:
                logger.warning(f"FMP Payment Required (402) for {endpoint}. Standard symbols only?")
                # Return empty to avoid retrying on 402
                return [] if "news" in endpoint or "calendar" in endpoint or "screener" in endpoint else {}
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"FMP API Error ({endpoint}): {e}")
            raise

    def get_stock_screener(self, market_cap_min: float = None, market: str = "US", limit: int = 100) -> List[Dict[str, Any]]:
        params = {}
        if market_cap_min:
            params["marketCapMoreThan"] = market_cap_min
        
        if market == "US":
            params["exchange"] = "NYSE,NASDAQ"
        elif market == "JP":
            params["exchange"] = "JPX"
        
        # Limit to reasonable number for testing/safety
        params["limit"] = limit
        
        return self._get("company-screener", params)

    def get_quote(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch quotes individually as batching is restricted on Stable/Starter plan."""
        results = []
        for sym in symbols:
            try:
                # Use query parameter style for stable/quote
                data = self._get("quote", params={"symbol": sym})
                if data and isinstance(data, list):
                    results.extend(data)
            except FMPPaymentRequiredError:
                # Silently catch 402 and continue so fetcher can fallback
                continue
            except Exception as e:
                logger.warning(f"Failed to fetch quote for {sym} via FMP: {e}")
        return results

    def get_index_quote(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Starter Plan uses stable/quote for indices as well."""
        return self.get_quote(symbols)

    def get_historical_daily(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        # Stable endpoint: historical-price-eod/full
        # Adding from/to parameters to see if they are supported by stable API
        params = {
            "symbol": symbol,
            "from": start_date,
            "to": end_date
        }
        data = self._get("historical-price-eod/full", params)
        
        if isinstance(data, list):
            # Filter manually just in case API ignores from/to
            filtered_data = [d for d in data if start_date <= d.get("date", "") <= end_date]
            return filtered_data
        return []

    def get_earnings_calendar(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        return self._get("earnings-calendar")

    def get_analyst_estimates(self, symbol: str) -> List[Dict[str, Any]]:
        # Analysts might not be in stable yet, but trying to follow the pattern
        return self._get(f"analyst-estimates/{symbol}") # Fallback if not in stable

    def get_news(self, tickers: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        # Use stable/news/stock-latest with symbols
        params = {
            "limit": limit,
            "tickers": ",".join(tickers)
        }
        return self._get("news/stock-latest", params)

    def get_general_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        return self._get("news/general-latest", params)
