import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .config import settings
from .fmp_provider import FMPProvider
from .logger_setup import logger

class WatchlistManager:
    """
    Manages the list of stocks and indices to track.
    Automatically updates and caches the list.
    """
    WATCHLIST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "watchlist.json")

    def __init__(self, provider: FMPProvider):
        self.provider = provider
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.WATCHLIST_PATH), exist_ok=True)
        self.data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.WATCHLIST_PATH):
            try:
                with open(self.WATCHLIST_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load watchlist cache: {e}")
        return {"last_updated": None, "stocks": []}

    def _save_cache(self):
        try:
            with open(self.WATCHLIST_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save watchlist cache: {e}")

    def update_watchlist(self, force: bool = False):
        """Update the watchlist if it's older than 7 days or forced."""
        now = datetime.now()
        last_updated_str = self.data.get("last_updated")
        
        should_update = force
        if not last_updated_str:
            should_update = True
        else:
            last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d")
            if now - last_updated > timedelta(days=7):
                should_update = True
        
        if not should_update:
            logger.info("Watchlist is up to date.")
            return

        logger.info("Updating watchlist via FMP Stock Screener...")
        stocks = []
        
        # 1. Fetch US Stocks (Top 20 by Market Cap)
        # Using a slightly lower min to ensure we get enough candidates
        us_results = self.provider.get_stock_screener(market_cap_min=100000000000, market="US", limit=100)
        us_sorted = sorted(us_results, key=lambda x: x.get("marketCap", 0), reverse=True)[:20]
        for s in us_sorted:
            stocks.append({
                "symbol": s["symbol"],
                "name": s["companyName"],
                "market": "US",
                "market_cap": s["marketCap"],
                "source": "fmp"
            })

        # 2. Fetch Japan Stocks (Top 20 by Market Cap)
        # Japanese market cap from FMP can be in JPY or USD depending on endpoint, 
        # but company-screener usually returns consistent values.
        jp_results = self.provider.get_stock_screener(market_cap_min=1000000000000, market="JP", limit=100)
        
        # Mapping for Japanese names (JP stocks ONLY)
        name_map = {
            # JP Stocks (added for FMP results)
            "7203.T": "トヨタ自動車",
            "8306.T": "三菱UFJフィナンシャルG",
            "6758.T": "ソニーグループ",
            "9432.T": "日本電信電話",
            "6861.T": "キーエンス",
            "9984.T": "ソフトバンクグループ",
            "8058.T": "三菱商事",
            "8316.T": "三井住友フィナンシャルG",
            "4063.T": "信越化学工業",
            "8035.T": "東京エレクトロン",
            "6501.T": "日立製作所",
            "8411.T": "みずほフィナンシャルG",
            "7974.T": "任天堂",
            "4502.T": "武田薬品工業",
            "4568.T": "第一三共",
            "6098.T": "リクルートHD",
            "7267.T": "本田技研工業",
            "8001.T": "伊藤忠商事",
            "9433.T": "KDDI",
            "9983.T": "ファーストリテイリング"
        }

        if not jp_results:
            logger.warning("FMP JP screener failed. Using hardcoded Top 20 Japanese stocks as fallback.")
            # Hardcoded top 20 by market cap (names are already JP)
            fallback_jp = [
                {"symbol": "7203.T", "name": "トヨタ自動車"},
                {"symbol": "8306.T", "name": "三菱UFJフィナンシャルG"},
                {"symbol": "6758.T", "name": "ソニーグループ"},
                {"symbol": "9432.T", "name": "日本電信電話"},
                {"symbol": "6861.T", "name": "キーエンス"},
                {"symbol": "9984.T", "name": "ソフトバンクグループ"},
                {"symbol": "8058.T", "name": "三菱商事"},
                {"symbol": "8316.T", "name": "三井住友フィナンシャルG"},
                {"symbol": "4063.T", "name": "信越化学工業"},
                {"symbol": "8035.T", "name": "東京エレクトロン"},
                {"symbol": "6501.T", "name": "日立製作所"},
                {"symbol": "8411.T", "name": "みずほフィナンシャルG"},
                {"symbol": "7974.T", "name": "任天堂"},
                {"symbol": "4502.T", "name": "武田薬品工業"},
                {"symbol": "4568.T", "name": "第一三共"},
                {"symbol": "6098.T", "name": "リクルートHD"},
                {"symbol": "7267.T", "name": "本田技研工業"},
                {"symbol": "8001.T", "name": "伊藤忠商事"},
                {"symbol": "9433.T", "name": "KDDI"},
                {"symbol": "9983.T", "name": "ファーストリテイリング"}
            ]
            for item in fallback_jp:
                stocks.append({
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "market": "JP",
                    "market_cap": 0,
                    "source": "yfinance"
                })
        else:
            jp_sorted = sorted(jp_results, key=lambda x: x.get("marketCap", 0), reverse=True)[:20]
            for s in jp_sorted:
                sym = s["symbol"]
                stocks.append({
                    "symbol": sym,
                    "name": name_map.get(sym, s["companyName"]),
                    "market": "JP",
                    "market_cap": s["marketCap"],
                    "source": "yfinance"
                })

        # Apply name mapping to US stocks too
        for s in stocks:
            if s["market"] == "US":
                s["name"] = name_map.get(s["symbol"], s["name"])

        self.data["last_updated"] = now.strftime("%Y-%m-%d")
        self.data["stocks"] = stocks
        self._save_cache()
        logger.info(f"Watchlist updated: {len(stocks)} stocks.")

    def get_watchlist(self) -> List[Dict[str, Any]]:
        return self.data.get("stocks", [])

    def get_all_symbols(self) -> List[str]:
        stock_symbols = [s["symbol"] for s in self.get_watchlist()]
        index_symbols = [i["symbol"] for i in settings.indices]
        return list(set(stock_symbols + index_symbols))
