import pandas as pd
import numpy as np
from analytics.indicators import (
    compute_sma, compute_ema, compute_rsi, compute_macd, 
    compute_bollinger_bands, compute_atr, compute_obv
)

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate ML features using strictly historical data (no lookahead bias).
    Target variable (next day log return) is also calculated but shifted correctly.
    """
    df = df.copy()
    
    # Lagged returns
    for lag in [1, 2, 3, 5, 10]:
        df[f'ret_{lag}d'] = df['Close'].pct_change(lag)
    
    # Log return
    df['log_ret'] = np.log(df['Close'] / df['Close'].shift(1))
    
    # SMA / EMA Ratios
    sma20 = compute_sma(df['Close'], 20)
    sma50 = compute_sma(df['Close'], 50)
    df['price_sma20_ratio'] = df['Close'] / sma20
    df['price_sma50_ratio'] = df['Close'] / sma50
    df['sma20_sma50_ratio'] = sma20 / sma50
    
    # Oscillators
    df['rsi_14'] = compute_rsi(df['Close'], 14)
    _, _, macd_hist = compute_macd(df['Close'])
    df['macd_hist'] = macd_hist
    
    # Bollinger Bands
    upper, mid, lower = compute_bollinger_bands(df['Close'], 20, 2)
    df['bb_pct_b'] = (df['Close'] - lower) / (upper - lower + 1e-8)
    df['bb_width'] = (upper - lower) / mid
    
    # Volatility
    atr14 = compute_atr(df['High'], df['Low'], df['Close'], 14)
    df['atr_price_ratio'] = atr14 / df['Close']
    
    # Volume
    vol20 = compute_sma(df['Volume'], 20)
    df['vol_20d_ratio'] = df['Volume'] / vol20
    
    # OBV slope (5 day)
    obv = compute_obv(df['Close'], df['Volume'])
    df['obv_slope'] = obv.diff(5)
    
    # Cyclical features
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 5)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 5)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    # ALL features up to this point use data up to time t.
    # Therefore, to predict time t+1, we shift the target.
    # Target: next day's log return.
    df['target'] = np.log(df['Close'].shift(-1) / df['Close'])
    
    # STRICT SHIFT DISCIPLINE
    # We must ensure that the features at index 'i' are ONLY available after day 'i' closes.
    # In standard scikit-learn format, X_i -> y_i. Our X_i are already constructed from data up to i.
    # Our y_i is 'target' which uses i+1. So this is safe for X_i -> y_i.
    
    return df
