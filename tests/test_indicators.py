import pytest
import pandas as pd
import numpy as np
from analytics.indicators import compute_sma, compute_rsi, compute_bollinger_bands, compute_macd

def test_compute_sma():
    series = pd.Series([1, 2, 3, 4, 5])
    sma = compute_sma(series, window=3)
    assert np.isnan(sma.iloc[0])
    assert np.isnan(sma.iloc[1])
    assert sma.iloc[2] == 2.0
    assert sma.iloc[4] == 4.0

def test_compute_rsi():
    # Downward trend -> RSI 0
    down = pd.Series([100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0, -10, -20, -30, -40, -50])
    rsi_down = compute_rsi(down, window=14)
    assert rsi_down.iloc[-1] < 1.0
    
    # Upward trend -> RSI 100
    up = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160])
    rsi_up = compute_rsi(up, window=14)
    assert rsi_up.iloc[-1] > 99.0

def test_compute_bollinger_bands():
    series = pd.Series([10]*25)
    upper, mid, lower = compute_bollinger_bands(series, window=20)
    assert upper.iloc[-1] == 10.0
    assert mid.iloc[-1] == 10.0
    assert lower.iloc[-1] == 10.0

def test_compute_macd():
    series = pd.Series([10]*50)
    macd_line, sig_line, macd_hist = compute_macd(series)
    assert abs(macd_line.iloc[-1]) < 1e-5
    assert abs(sig_line.iloc[-1]) < 1e-5
    assert abs(macd_hist.iloc[-1]) < 1e-5
