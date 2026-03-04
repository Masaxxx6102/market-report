import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os
import mplfinance as mpf
from datetime import datetime
from typing import List, Dict, Any
from .fmp_provider import StockDataProvider
from .logger_setup import logger

class ChartGenerator:
    """
    Generates PNG candlestick charts for market indices using mplfinance.
    """
    CHART_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "charts")

    def __init__(self, providers: Dict[str, StockDataProvider]):
        self.providers = providers
        if not os.path.exists(self.CHART_DIR):
            os.makedirs(self.CHART_DIR)
        
        # Professional settings with robust Japanese font fallback to prevent mojibake
        # List of Japanese fonts to try (Windows, Mac, Linux)
        self.jp_fonts = ['Meiryo', 'MS Gothic', 'Hiragino Sans', 'AppleGothic', 'IPAGothic', 'IPAMincho', 'IPAexGothic', 'DejaVu Sans', 'Noto Sans JP', 'sans-serif']
        plt.rcParams['font.sans-serif'] = self.jp_fonts
        plt.rcParams['axes.unicode_minus'] = False

    def generate_index_charts(self, symbol: str, name: str, source: str = "fmp") -> Dict[str, str]:
        """
        Generate both long-term (Monthly, Max Hist) and short-term (Weekly, 1y) candlestick charts.
        Returns paths to generated images.
        """
        logger.info(f"Generating professional candlestick charts for {name} ({symbol})...")
        
        provider = self.providers.get(source)
        if not provider:
            logger.error(f"Provider {source} not found for {symbol}")
            return {}

        # Fetch maximum available history for indices (30+ years if possible)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date_long = "1990-01-01" # Fetch as far back as possible
        
        hist_data = provider.get_historical_daily(symbol, start_date_long, end_date)
        
        if not hist_data and source != "yfinance":
            yf_provider = self.providers.get("yfinance")
            if yf_provider:
                logger.info(f"Primary provider {source} failed for {symbol} history. Falling back to yfinance.")
                hist_data = yf_provider.get_historical_daily(symbol, "1980-01-01", end_date)

        if not hist_data:
            logger.warning(f"No historical data for {symbol} via any provider, skipping charts.")
            return {}

        df = pd.DataFrame(hist_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.set_index('date')
        
        # Mapping col names to OHLC format for mplfinance
        cols = {'close': 'Close', 'open': 'Open', 'high': 'High', 'low': 'Low', 'volume': 'Volume'}
        df = df.rename(columns=lambda x: cols.get(x.lower(), x))

        date_str = datetime.now().strftime("%Y-%m-%d")
        long_path = os.path.join(self.CHART_DIR, f"long_{symbol}_{date_str}.png")
        short_path = os.path.join(self.CHART_DIR, f"short_{symbol}_{date_str}.png")

        # 1. Short Term: Weekly Candles, 1 year
        start_short = datetime.now() - pd.DateOffset(years=1)
        df_short_daily = df[df.index >= start_short]
        if not df_short_daily.empty:
            df_short_weekly = df_short_daily.resample('W').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
            # Explicit start date label
            actual_start_short = df_short_weekly.index[0].strftime("%Y年%m月")
            self._plot_candlestick(df_short_weekly, f"{name} (週足/1年)", short_path, subtitle=f"{actual_start_short}〜")
        
        # 2. Long Term: Monthly Candles, Max History
        df_long_monthly = df.resample('ME').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna()
        # Explicit start date label
        actual_start_long = df_long_monthly.index[0].strftime("%Y年%m月")
        self._plot_candlestick(df_long_monthly, f"{name} (月足/長期)", long_path, subtitle=f"{actual_start_long}〜")

        return {"long": long_path, "short": short_path}

    def _plot_candlestick(self, df: pd.DataFrame, title: str, path: str, subtitle: str = ""):
        """
        Internal method to plot candlestick charts using mplfinance.
        """
        # Identify available font to use for explicit setting
        active_font = self.jp_fonts[0] # Default to Meiryo

        # Customize style: professional dark/grid
        mc = mpf.make_marketcolors(up='red', down='green', edge='inherit', wick='inherit', volume='in', inherit=True)
        s = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, gridstyle='--', y_on_right=False)
        
        # Prepare figure
        fig, axes = mpf.plot(df, type='candle', style=s, 
                           volume=True, returnfig=True, figsize=(12, 8), # Slightly larger figure
                           datetime_format='%Y/%m', xrotation=0) 
        
        # Title and explicit start date label
        ax1 = axes[0]
        # Explicitly setting fontname can sometimes bypass rcParams issues
        ax1.set_title(title, fontsize=28, fontweight='bold', pad=50, fontname=active_font)
        
        if subtitle:
            # Use red/bold for the start date to make it super clear
            ax1.text(0, 1.08, f"開始時期: {subtitle}", transform=ax1.transAxes, 
                    ha='left', fontsize=20, color='#D32F2F', fontweight='bold', fontname=active_font)

        # Formatting: Significantly larger ticks for readability
        ax1.tick_params(axis='both', which='major', labelsize=18)
        ax1.yaxis.label.set_size(18)
        
        if len(axes) > 2: # Volume axis
            axes[2].tick_params(labelsize=14)
            # Volume label if exists
            axes[2].yaxis.label.set_size(14)
        
        # Ensure tight layout to prevent label clipping
        plt.savefig(path, dpi=120, bbox_inches='tight') # Lower DPI with larger figsize for balanced Word insertion
        plt.close(fig)
