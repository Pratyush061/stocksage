import pandas as pd
import numpy as np

def calculate_risk_metrics(returns: pd.Series, risk_free_rate: float = 0.06) -> dict:
    # Annualized return (assuming 252 trading days)
    total_return = (1 + returns).prod() - 1
    
    # Check for NaNs or negative total returns that make CAGR complex
    days = len(returns)
    cagr = (1 + total_return) ** (252 / max(days, 1)) - 1 if days > 0 else 0
    
    daily_rf = risk_free_rate / 252
    excess_returns = returns - daily_rf
    
    ann_vol = returns.std() * np.sqrt(252)
    sharpe = excess_returns.mean() / (returns.std() + 1e-8) * np.sqrt(252)
    
    downside_returns = returns[returns < 0]
    downside_vol = downside_returns.std() * np.sqrt(252)
    sortino = excess_returns.mean() / (downside_returns.std() + 1e-8) * np.sqrt(252) if len(downside_returns) > 0 else 0
    
    cum_returns = (1 + returns).cumprod()
    running_max = np.maximum.accumulate(cum_returns)
    drawdowns = (cum_returns - running_max) / running_max
    max_drawdown = drawdowns.min()
    
    win_rate = len(returns[returns > 0]) / max(len(returns[returns != 0]), 1)
    
    return {
        'total_return': total_return,
        'cagr': cagr,
        'ann_vol': ann_vol,
        'sharpe': sharpe,
        'sortino': sortino,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate
    }

def run_backtest(df: pd.DataFrame, signals: pd.Series, cost_pct: float = 0.001, slippage_pct: float = 0.0003):
    """
    Vectorized backtest engine.
    signals: 1 for long, 0 for flat.
    Signals generated at close of day t are executed at open of day t+1.
    """
    # Shift signals so that signal at t determines position at t+1
    positions = signals.shift(1).fillna(0)
    
    # Calculate daily returns based on position
    # Return from Open(t) to Close(t) if we entered at Open(t)
    # However, standard vectorized backtest assumes we hold from Close(t-1) to Close(t)
    # For a truer execution, if position changes, we pay costs.
    daily_ret = df['Close'].pct_change()
    
    # Strategy returns before costs
    strat_ret = positions * daily_ret
    
    # Turnover (position changes)
    trades = positions.diff().abs().fillna(0)
    
    # Costs applied when trades happen
    costs = trades * (cost_pct + slippage_pct)
    
    strat_ret_net = strat_ret - costs
    
    metrics = calculate_risk_metrics(strat_ret_net.dropna())
    metrics['trade_count'] = trades.sum()
    
    # B&H metrics
    bh_ret = daily_ret.fillna(0)
    bh_metrics = calculate_risk_metrics(bh_ret)
    
    return {
        'equity_curve': (1 + strat_ret_net.fillna(0)).cumprod(),
        'bh_equity_curve': (1 + bh_ret).cumprod(),
        'metrics': metrics,
        'bh_metrics': bh_metrics
    }
