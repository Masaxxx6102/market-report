from datetime import datetime, timedelta
from typing import List, Dict, Any
from .fmp_provider import FMPProvider
from .logger_setup import logger

class EarningsDataFetcher:
    """
    Fetches earnings, analyst estimates, and rating changes.
    """
    def __init__(self, provider: FMPProvider):
        self.provider = provider

    def fetch_earnings_events(self, symbols: List[str], days_lookback: int = 1) -> List[Dict[str, Any]]:
        """Fetch earnings reports for the given symbols within a timeframe."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_lookback)).strftime("%Y-%m-%d")
        
        all_earnings = self.provider.get_earnings_calendar(start_date, end_date)
        
        # Filter by symbols of interest
        symbol_set = set(symbols)
        relevant_earnings = []
        
        for event in all_earnings:
            if event["symbol"] in symbol_set and event.get("eps"):
                eps_actual = event.get("eps", 0)
                eps_estimated = event.get("epsEstimated", 0)
                
                # Simple surprise calculation if not provided
                surprise_pct = 0.0
                if eps_estimated:
                    surprise_pct = ((eps_actual - eps_estimated) / abs(eps_estimated)) * 100
                
                result = "In-line"
                if surprise_pct > 2: result = "Beat"
                elif surprise_pct < -2: result = "Miss"
                
                relevant_earnings.append({
                    "symbol": event["symbol"],
                    "name": event.get("date"), # Calendar doesn't always have name, handle in report
                    "reported_eps": eps_actual,
                    "consensus_eps": eps_estimated,
                    "surprise_pct": surprise_pct,
                    "result": result,
                    "reported_revenue": event.get("revenue", 0),
                    "consensus_revenue": event.get("revenueEstimated", 0)
                })
        
        return relevant_earnings

    def fetch_revisions_and_ratings(self, symbols: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch revisions and rating changes for symbols. 
        Note: Detailed revision detection requires historical comparison not yet implemented broadly.
        """
        # For simplicity in this iteration, we focus on the most recent entries
        # Real-time revision detection would need to compare with yesterday's crawl.
        return {
            "estimate_revisions": [],
            "rating_changes": [],
            "capex_events": []
        }
