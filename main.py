import os
import shutil
import certifi
import json

import platform

# Workaround for Unicode paths in SSL certificates (Windows only)
if platform.system() == "Windows":
    safe_cert_path = "C:/Users/Public/cacert.pem"
    try:
        import shutil
        import certifi
        shutil.copy(certifi.where(), safe_cert_path)
        os.environ['CURL_CA_BUNDLE'] = safe_cert_path
        os.environ['SSL_CERT_FILE'] = safe_cert_path
        os.environ['REQUESTS_CA_BUNDLE'] = safe_cert_path
    except Exception:
        pass
else:
    # Linux/GitHub Actions environment - certificates are usually standard
    os.environ['PYTHONHTTPSVERIFY'] = '1' # Standard verification

os.environ['PYTHONHTTPSVERIFY'] = '0'
import sys
from datetime import datetime
from src.config import settings
from src.logger_setup import logger
from src.fmp_provider import FMPProvider
from src.watchlist import WatchlistManager
from src.stock_data import StockDataFetcher
from src.earnings_data import EarningsDataFetcher
from src.news_fetcher import NewsFetcher
from src.news_filter import NewsFilterAI
from src.chart_generator import ChartGenerator
from src.report_builder import ReportBuilder
from src.email_sender import GmailSender
from src.base_provider import StockDataProvider

import time
from datetime import datetime, timedelta, timezone
import argparse

def main():
    parser = argparse.ArgumentParser(description="Daily Market Report")
    parser.add_argument("--schedule", action="store_true", help="Run in scheduler mode")
    args = parser.parse_args()

    if args.schedule:
        target_time = settings.delivery_time
        logger.info(f"Report scheduled for {target_time} daily. Starting monitoring loop...")
        
        last_run_date = ""
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.strftime("%Y-%m-%d")

            if current_time == target_time and current_date != last_run_date:
                logger.info(f"Target time {target_time} reached. Starting report generation...")
                run_report()
                last_run_date = current_date
                logger.info("Report task finished. Waiting for next day...")
            
            time.sleep(30) # Check every 30 seconds
    else:
        run_report()

def run_report():
    logger.info("Starting Daily Market Report process...")
    try:
        # Step 0: Initialize Providers
        fmp_key = settings.api_keys.get("fmp")
        gemini_key = settings.api_keys.get("gemini")
        if not fmp_key:
            logger.error("FMP API Key not found in config.yaml")
            return

        from src.yfinance_provider import YFinanceProvider
        fmp_provider = FMPProvider(fmp_key)
        yf_provider = YFinanceProvider()
        
        providers = {
            "fmp": fmp_provider,
            "yfinance": yf_provider
        }
        
        # Step 1: Watchlist
        watchlist_mgr = WatchlistManager(fmp_provider)
        watchlist_mgr.update_watchlist(force=True)
        watchlist_data = watchlist_mgr.get_watchlist()
        
        # Build symbol list
        all_items = []
        for s in watchlist_data:
            all_items.append({"symbol": s["symbol"], "source": s.get("source", "fmp")})
        for idx in settings.indices:
            all_items.append({"symbol": idx["symbol"], "source": idx.get("source", "fmp")})

        # Step 2: Fetch Quotes
        fetcher = StockDataFetcher(providers)
        quotes = fetcher.fetch_market_quotes(all_items)

        # Step 3: Fetch Earnings
        earnings_fetcher = EarningsDataFetcher(fmp_provider)
        stock_symbols = [s["symbol"] for s in watchlist_data]
        earnings = earnings_fetcher.fetch_earnings_events(stock_symbols)

        # Step 4: News & AI
        news_fetcher = NewsFetcher(fmp_provider)
        filtered_news = []
        market_overview = {}
        if gemini_key and gemini_key != "YOUR_GEMINI_API_KEY":
            filter_ai = NewsFilterAI(gemini_key)
            raw_news = news_fetcher.fetch_all_news(stock_symbols)
            filtered_news = filter_ai.filter_news(raw_news, stock_symbols)
            market_overview = filter_ai.generate_market_overview(raw_news, quotes)
        else:
            logger.warning("Gemini key not configured.")
            raw_news = news_fetcher.fetch_all_news(stock_symbols) 
            filtered_news = raw_news[:10]

        # Step 5: Charts
        charts = {}
        chart_gen = ChartGenerator(providers)
        for idx in settings.indices:
            if idx.get("skip_chart"):
                continue
            res = chart_gen.generate_index_charts(idx["symbol"], idx["name"], source=idx.get("source", "fmp"))
            if res:
                charts[idx["name"]] = res

        # Step 6: Build Report
        name_lookup = {s["symbol"]: s["name"] for s in watchlist_data}
        for idx in settings.indices:
            name_lookup[idx["symbol"]] = idx["name"]
        for sym, q in quotes.items():
            if sym in name_lookup:
                q["name"] = name_lookup[sym]

        report_data = {
            "quotes": quotes,
            "earnings": earnings,
            "news": filtered_news,
            "charts": charts,
            "overview": market_overview
        }
        builder = ReportBuilder(organization=settings.organization)
        report_path = builder.build_report(report_data)
        
        # Step 6.5: Export for Web Dashboard
        generate_web_data(report_data)

        # Step 7: Send Email
        email_data = settings.email_settings
        recipients = email_data.get("recipients", [])
        subject = email_data.get("subject_template", "Daily Market Report {date}").format(date=datetime.now().strftime("%Y-%m-%d"))
        
        logger.info(f"Targeting {len(recipients)} recipients: {recipients}")
        if not report_path:
            logger.error("Report path is empty. Report generation might have failed internally.")
        
        if report_path and recipients:
            logger.info(f"Attempting to send email with attachment: {report_path}")
            email_sender = GmailSender()
            success = email_sender.send_report(
                to_emails=recipients,
                subject=subject,
                body=f"本日のマーケットレポートを添付いたします。\n\nWeb版ダッシュボードはこちら：\nhttps://masaxxx6102.github.io/market-report/\n\n（※最新の市場データを確認するには、上記URLにアクセスしてください）",
                attachment_path=report_path
            )
            if success:
                logger.info("Email delivery triggered successfully.")
            else:
                logger.error("Email delivery failed at the sender level.")
        else:
            logger.warning(f"Skipping email send. Path exists: {bool(report_path)}, Recipients count: {len(recipients)}")
        
        logger.info("Process completed successfully.")
    except Exception as e:
        logger.exception(f"Error: {e}")

def generate_web_data(report_data):
    """
    Exports market data to a JSON file for the Web Dashboard.
    """
    web_data_path = os.path.join(os.path.dirname(__file__), "data", "latest_report.json")
    os.makedirs(os.path.dirname(web_data_path), exist_ok=True)
    
    # Ensure charts paths are relative for the web app
    # (Assuming index.html is in the root and charts/ is in the root/data/charts or similar)
    # The current code puts charts in <root>/charts
    
    # Use JST (Japan Standard Time) for the sync timestamp
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    
    serializable_data = {
        "last_updated": now_jst.strftime("%Y-%m-%d %H:%M:%S"),
        "quotes": report_data["quotes"],
        "news": report_data["news"],
        "charts": report_data["charts"],
        "overview": report_data["overview"]
    }
    
    with open(web_data_path, "w", encoding="utf-8") as f:
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Web Dashboard data exported to {web_data_path}")

if __name__ == "__main__":
    main()
