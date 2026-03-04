import json
import os
from datetime import datetime
from typing import List, Dict, Any
from .base_provider import StockDataProvider
from .fmp_provider import FMPProvider
from .logger_setup import logger

class StockDataFetcher:
    """
    Fetches real-time and historical price data for stocks and indices.
    Manages caching of year-start prices.
    """
    YEAR_START_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "year_start_prices.json")

    def __init__(self, providers: Dict[str, StockDataProvider]):
        self.providers = providers
        self.year_start_cache = self._load_year_start_cache()

    def _load_year_start_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.YEAR_START_CACHE_PATH):
            try:
                with open(self.YEAR_START_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load year start cache: {e}")
        return {}

    def _save_year_start_cache(self):
        try:
            with open(self.YEAR_START_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.year_start_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save year start cache: {e}")

    def get_year_start_price(self, symbol: str, source: str = "fmp") -> float:
        """Get the price as of the beginning of the current year."""
        current_year = datetime.now().year
        cache_key = f"{symbol}_{current_year}"
        
        if cache_key in self.year_start_cache:
            return self.year_start_cache[cache_key]
        
        provider = self.providers.get(source)
        if not provider:
            logger.error(f"Provider {source} not found for {symbol}")
            return 0.0

        # Fetch from API: Try first few days of January
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-01-10"
        
        try:
            hist = provider.get_historical_daily(symbol, start_date, end_date)
            if hist:
                # Historical results are usually sorted by date (newest first or oldest first)
                # We want the oldest one in the range
                oldest = sorted(hist, key=lambda x: x["date"])[0]
                price = oldest["close"]
                self.year_start_cache[cache_key] = price
                self._save_year_start_cache()
                return price
        except Exception as e:
            logger.warning(f"Failed to fetch historical data for {symbol}: {e}")
        
        return 0.0

    def fetch_market_quotes(self, watchlist_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes and enrich with year-to-date performance."""
        # Group symbols by provider and store names
        by_source = {}
        names_map = {}
        for item in watchlist_data:
            source = item.get("source", "fmp")
            sym = item["symbol"]
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(sym)
            if "name" in item:
                names_map[sym] = item["name"]

        enriched_quotes = {}
        for source, symbols in by_source.items():
            provider = self.providers.get(source)
            if not provider:
                logger.error(f"Provider for {source} not configured.")
                continue
            
            # Fetch quotes from primary provider
            raw_results = provider.get_quote(symbols)
            results_map = {q["symbol"]: q for q in raw_results}
            
            # Identify missing symbols and try fallback
            for sym in symbols:
                q = results_map.get(sym)
                used_source = source
                
                if not q and source != "yfinance":
                    yf_provider = self.providers.get("yfinance")
                    if yf_provider:
                        logger.info(f"Falling back to yfinance for {sym} quote...")
                        yf_results = yf_provider.get_quote([sym])
                        if yf_results:
                            q = yf_results[0]
                            used_source = "yfinance"

                if not q:
                    logger.warning(f"Could not retrieve quote for {sym} via any provider.")
                    continue

                close = q["price"]
                prev_close = q.get("previousClose", close)
                
                ytd_start = self.get_year_start_price(sym, source=used_source)
                ytd_change = close - ytd_start if ytd_start else 0.0
                ytd_pct = (ytd_change / ytd_start * 100) if ytd_start else 0.0
                
                enriched_quotes[sym] = {
                    "symbol": sym,
                    "name": names_map.get(sym, q.get("name", sym)),
                    "price": close,
                    "change": q.get("change", 0),
                    "changesPercentage": q.get("changesPercentage", q.get("changePercentage", 0)),
                    "previousClose": prev_close,
                    "yearStart": ytd_start,
                    "ytdChange": ytd_change,
                    "ytdChangePercentage": ytd_pct
                }
        
        return enriched_quotes
