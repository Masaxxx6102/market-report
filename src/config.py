import yaml
import os
from pathlib import Path

class Config:
    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            # In GitHub Actions, we might not have a config.yaml
            # We'll rely on environment variables instead.
            return {}
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else {}

    @property
    def api_keys(self):
        # Prioritize environment variables for GitHub Actions
        keys = self.data.get("api_keys", {})
        if os.environ.get("FMP_API_KEY"):
            keys["fmp"] = os.environ.get("FMP_API_KEY")
        if os.environ.get("GEMINI_API_KEY"):
            keys["gemini"] = os.environ.get("GEMINI_API_KEY")
        return keys

    @property
    def email_settings(self):
        email = self.data.get("email", {})
        if os.environ.get("GMAIL_SENDER"):
            email["sender"] = os.environ.get("GMAIL_SENDER")
        if os.environ.get("GMAIL_RECIPIENTS"):
            email["recipients"] = [r.strip() for r in os.environ.get("GMAIL_RECIPIENTS").split(",")]
        return email

    @property
    def market_cap_filters(self):
        return self.data.get("market_cap_filters", {})

    @property
    def indices(self):
        default_indices = [
            {"symbol": "^N225", "name": "日経平均", "source": "yfinance"},
            {"symbol": "TOPIX", "name": "TOPIX", "source": "yfinance", "skip_chart": True},
            {"symbol": "^GSPC", "name": "S&P500", "source": "fmp"},
            {"symbol": "^IXIC", "name": "NASDAQ", "source": "fmp"},
            {"symbol": "^DJI", "name": "DOW", "source": "fmp"},
            {"symbol": "^GDAXI", "name": "DAX", "source": "fmp"},
            {"symbol": "^FTSE", "name": "FTSE100", "source": "fmp"},
            {"symbol": "^STOXX", "name": "STOXX600", "source": "fmp"}
        ]
        return self.data.get("indices", default_indices)

    @property
    def organization(self):
        return self.data.get("organization", "Forcus株式会社")

    @property
    def report_title(self):
        return self.data.get("report_title", "Daily Market Report")

    @property
    def timezone(self):
        return self.data.get("timezone", "Asia/Tokyo")

    @property
    def delivery_time(self):
        return self.data.get("delivery_time", "08:00")

# Singleton instance
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
settings = Config(config_path)
