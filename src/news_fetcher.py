from typing import List, Dict, Any
from .fmp_provider import FMPProvider
from .logger_setup import logger

class NewsFetcher:
    """
    Fetches news from various sources (FMP, and placeholder for QUICK).
    """
    def __init__(self, provider: FMPProvider):
        self.provider = provider

    def fetch_all_news(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """
        Combine macro news and individual stock news.
        """
        logger.info(f"Fetching news for {len(tickers)} tickers + general market news...")
        
        # Batch tickers to avoid huge URLs if needed (FMP handles many, but let's be safe)
        all_news = []
        batch_size = 30
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i+batch_size]
            stock_news = self.provider.get_news(batch, limit=500)
            all_news.extend(stock_news)
            
        general_news = self.provider.get_general_news(limit=500)
        all_news.extend(general_news)
        
        # De-duplicate by URL/Title
        unique_news = []
        seen_urls = set()
        for item in all_news:
            url = item.get("url")
            if url and url not in seen_urls:
                unique_news.append({
                    "headline": item.get("title") or item.get("headline"),
                    "summary": item.get("text") or item.get("summary"),
                    "source": item.get("site") or item.get("source"),
                    "url": url,
                    "date": item.get("publishedDate") or item.get("date"),
                    "related_symbols": item.get("tickers") or []
                })
                seen_urls.add(url)
                
        logger.info(f"Retrieved {len(unique_news)} unique news items.")
        return unique_news
