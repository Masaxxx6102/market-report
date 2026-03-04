import yaml
import os
from pathlib import Path

class Config:
    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

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
        return self.data.get("indices", [])

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
