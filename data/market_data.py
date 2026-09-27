import yfinance as yf
import pandas as pd
import numpy as np
import time
from flask_caching import Cache
from dash import Dash
import logging

logger = logging.getLogger(__name__)

# Cache setup to be initialized in app.py
cache = Cache()

def init_cache(app: Dash):
    cache.init_app(app.server, config={
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR': 'cache-directory',
        'CACHE_DEFAULT_TIMEOUT': 900 # 15 minutes default
    })

def generate_mock_data(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """Generate synthetic stock data when yfinance fails (fallback for testing)."""
    np.random.seed(hash(symbol) % (2**32))
    
    # Map periods to days roughly
    days = 30
    if period == "1d": days = 1
    elif period == "5d": days = 5
    elif period == "1mo": days = 30
    elif period == "3mo": days = 90
    elif period == "6mo": days = 180
    elif period == "1y": days = 365
    elif period == "5y": days = 1825
    
    # Intraday handling (rough approximation)
    if interval == "15m":
        periods = days * 25 # ~25 15-min bars per day
        freq = '15min'
    else:
        periods = days
        freq = 'B'
        
    dates = pd.date_range(end=pd.Timestamp.today().normalize() + pd.Timedelta(hours=15, minutes=30), periods=periods, freq=freq)
    
    # Random walk
    returns = np.random.normal(0.0002, 0.01, size=len(dates))
    price = 1000 * np.exp(np.cumsum(returns))
    
    high = price * (1 + np.abs(np.random.normal(0, 0.005, size=len(dates))))
    low = price * (1 - np.abs(np.random.normal(0, 0.005, size=len(dates))))
    open_price = price * (1 + np.random.normal(0, 0.002, size=len(dates)))
    volume = np.random.randint(100000, 10000000, size=len(dates))
    
    df = pd.DataFrame({
        'Open': open_price,
        'High': high,
        'Low': low,
        'Close': price,
        'Volume': volume
    }, index=dates)
    
    return df

def fetch_data_with_retry(symbol: str, period: str = "1mo", interval: str = "1d", retries: int = 3, backoff: float = 1.0) -> pd.DataFrame:
    """Fetch yfinance data with exponential backoff retry logic. Falls back to mock data if yfinance fails."""
    for attempt in range(retries):
        try:
            df = yf.Ticker(symbol).history(period=period, interval=interval)
            if df is not None and not df.empty:
                df.index = df.index.tz_localize(None) # Remove timezone for consistency
                return df
            elif df is not None and df.empty:
                logger.warning(f"Empty dataframe returned for {symbol}")
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed for {symbol}: {e}")
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
            else:
                logger.error(f"All retries failed for {symbol}. Returning fallback mock data.")
    
    # Fallback to mock data to ensure app functionality when Yahoo Finance API is rate limiting/blocking
    logger.warning(f"Using mock data for {symbol} due to Yahoo Finance failure.")
    return generate_mock_data(symbol, period=period, interval=interval)

@cache.memoize(timeout=86400) # 24h for daily history
def get_daily_history(symbol: str, period: str = "5y") -> pd.DataFrame:
    """Fetch daily historical data."""
    return fetch_data_with_retry(symbol, period=period, interval="1d")

@cache.memoize(timeout=900) # 15 min for intraday pulse
def get_intraday_data(symbol: str, period: str = "1d", interval: str = "15m") -> pd.DataFrame:
    """Fetch intraday data for pulse overview."""
    return fetch_data_with_retry(symbol, period=period, interval=interval)

@cache.memoize(timeout=900)
def get_current_price_info(symbol: str) -> dict:
    """Get latest price and day change."""
    df = fetch_data_with_retry(symbol, period="5d", interval="1d")
    if df.empty or len(df) < 2:
        return {"close": 0.0, "change": 0.0, "change_pct": 0.0, "volume": 0}
    
    last_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    change = last_close - prev_close
    change_pct = (change / prev_close) * 100
    return {
        "close": float(last_close),
        "change": float(change),
        "change_pct": float(change_pct),
        "volume": int(df['Volume'].iloc[-1])
    }
