import pytest
import pandas as pd
import numpy as np
from analytics.backtest import calculate_risk_metrics, run_backtest

def test_calculate_risk_metrics():
    # 100 days of 1% daily return
    returns = pd.Series([0.01] * 100)
    metrics = calculate_risk_metrics(returns)
    
    assert metrics['win_rate'] == 1.0
    assert metrics['max_drawdown'] == 0.0
    
def test_run_backtest_no_signals():
    dates = pd.date_range('2023-01-01', periods=100)
    df = pd.DataFrame({
        'Close': np.linspace(100, 200, 100)
    }, index=dates)
    
    signals = pd.Series([0] * 100, index=dates)
    
    res = run_backtest(df, signals, cost_pct=0.0, slippage_pct=0.0)
    
    # Strategy should have 0 trades and 0 total return
    assert res['metrics']['trade_count'] == 0
    assert res['metrics']['total_return'] == 0.0

def test_run_backtest_costs():
    dates = pd.date_range('2023-01-01', periods=3)
    df = pd.DataFrame({
        'Close': [100, 100, 100]
    }, index=dates)
    
    # Buy on day 1 (signal on day 0, execute on day 1), Sell on day 2
    signals = pd.Series([1, 0, 0], index=dates)
    
    # Cost = 10% per trade (unrealistic but easy to test)
    res = run_backtest(df, signals, cost_pct=0.1, slippage_pct=0.0)
    
    # Trade count should be 2 (buy then sell)
    assert res['metrics']['trade_count'] == 2
    
    # Strategy return should be exactly negative the costs since price didn't change
    # Two trades of 10% cost = roughly 20% loss (compounded it's actually 1 - (0.9 * 0.9) approx)
    # Actually, the cost is applied additively to the return in our simple vectorized backtest.
    # Return at t=1 is 0 - 0.1 = -0.1
    # Return at t=2 is 0 - 0.1 = -0.1
    # Total return = (1-0.1)*(1-0.1) - 1 = 0.81 - 1 = -0.19
    assert np.isclose(res['metrics']['total_return'], -0.19)
