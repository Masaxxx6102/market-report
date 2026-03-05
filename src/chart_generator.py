import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os
import mplfinance as mpf
import japanize_matplotlib # Force Japanese font support
from datetime import datetime
from typing import List, Dict, Any
from .fmp_provider import StockDataProvider
from .logger_setup import logger

class ChartGenerator:
    """
    Generates PNG candlestick charts for market indices using mplfinance.
    Uses japanize-matplotlib for robust Japanese character support.
    """
    CHART_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "charts")

    def __init__(self, providers: Dict[str, StockDataProvider]):
        self.providers = providers
        if not os.path.exists(self.CHART_DIR):
            os.makedirs(self.CHART_DIR)
        
    def generate_index_charts(self, symbol: str, name: str, source: str = "fmp") -> Dict[str, str]:
        """
        Generate both long-term (Monthly, Max Hist) and short-term (Weekly, 1y) candlestick charts.
        """
        logger.info(f"Generating charts for {name} ({symbol})...")
        
        provider = self.providers.get(source)
        if not provider:
            logger.error(f"Provider {source} not found for {symbol}")
            return {}

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date_long = "1990-01-01"
        
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
        df = df.sort_values('date').set_index('date')
        
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
            self._plot_candlestick(df_short_weekly, f"{name} (週足/1年)", short_path, subtitle=f"{df_short_weekly.index[0].strftime('%Y/%m')}～")
        
        # 2. Long Term: Monthly Candles, Max History
        df_long_monthly = df.resample('ME').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna()
        self._plot_candlestick(df_long_monthly, f"{name} (月足/長期)", long_path, subtitle=f"{df_long_monthly.index[0].strftime('%Y/%m')}～")

        return {"long": long_path, "short": short_path}

    def _plot_candlestick(self, df: pd.DataFrame, title: str, path: str, subtitle: str = ""):
        """
        Internal method to plot candlestick charts with explicit font enforcement.
        """
        # Explicitly set the font to the one provided by japanize-matplotlib
        plt.rcParams['font.family'] = 'IPAexGothic'
        
        # Prepare style with market colors and explicit Japanese font family
        mc = mpf.make_marketcolors(up='#ff4444', down='#00c853', edge='inherit', wick='inherit', volume='in', inherit=True)
        # 'night' is not always available, using 'charles' as base and overriding to deep dark
        s = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, gridstyle='--', 
                             y_on_right=False, rc={'font.family': 'IPAexGothic', 'axes.facecolor': '#000000', 'figure.facecolor': '#000000', 'text.color': 'white', 'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white', 'grid.color': '#1f1f1f'})
        
        # Prepare figure (Removed invalid 'fontfamily' kwarg)
        fig, axes = mpf.plot(df, type='candle', style=s, 
                           volume=True, returnfig=True, figsize=(12, 8), 
                           datetime_format='%Y/%m', xrotation=0) 
        
        ax1 = axes[0]
        # Explicitly set font on title and text as well
        ax1.set_title(title, fontsize=28, fontweight='bold', pad=50, fontname='IPAexGothic')
        
        if subtitle:
            ax1.text(0, 1.08, f"開始時期: {subtitle}", transform=ax1.transAxes, 
                    ha='left', fontsize=20, color='#D32F2F', fontweight='bold', fontname='IPAexGothic')

        # Formatting
        ax1.tick_params(axis='both', which='major', labelsize=18)
        ax1.yaxis.label.set_size(18)
        if len(axes) > 2: 
            axes[2].tick_params(labelsize=14)
            axes[2].yaxis.label.set_size(14)
        
        plt.savefig(path, dpi=120, bbox_inches='tight')
        plt.close(fig)
