import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from data.market_data import get_daily_history
from data.nifty50 import NIFTY_50
from analytics.indicators import compute_sma, compute_rsi
from analytics.backtest import run_backtest
from components.loading import StyledLoading
from components.stat_card import StatCard
from components.disclaimer import Disclaimer

dash.register_page(__name__, path='/backtest', name='Strategy Backtest')

stock_options = [{"label": f"{s['symbol']} - {s['name']}", "value": s['symbol']} for s in NIFTY_50]

layout = html.Div([
    html.H2("Strategy Backtest Engine", style={"marginBottom": "24px"}),
    
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id="bt-stock",
                options=stock_options,
                value="RELIANCE.NS",
                className="dark-dropdown"
            )
        ], md=4),
        dbc.Col([
            dbc.Select(
                id="bt-strategy",
                options=[
                    {"label": "SMA Crossover (20/50)", "value": "sma"},
                    {"label": "RSI Mean Reversion (30/70)", "value": "rsi"},
                ],
                value="sma"
            )
        ], md=4),
        dbc.Col([
            dbc.Select(
                id="bt-period",
                options=[
                    {"label": "1 Year", "value": "1y"},
                    {"label": "3 Years", "value": "3y"},
                    {"label": "5 Years", "value": "5y"},
                ],
                value="5y"
            )
        ], md=4),
    ], style={"marginBottom": "24px"}),
    
    StyledLoading(html.Div(id="bt-results")),
    
    Disclaimer()
])

@callback(
    Output("bt-results", "children"),
    Input("bt-stock", "value"),
    Input("bt-strategy", "value"),
    Input("bt-period", "value")
)
def update_backtest(symbol, strategy, period):
    if not symbol:
        return html.Div()
        
    df = get_daily_history(symbol, period=period)
    if df.empty or len(df) < 55:
        return html.Div("Not enough data to backtest.", className="text-bear")
        
    # Generate Signals
    signals = pd.Series(0, index=df.index)
    
    if strategy == "sma":
        sma20 = compute_sma(df['Close'], 20)
        sma50 = compute_sma(df['Close'], 50)
        # 1 when SMA20 > SMA50, 0 otherwise
        signals = (sma20 > sma50).astype(int)
    elif strategy == "rsi":
        rsi = compute_rsi(df['Close'])
        # Simplified mean reversion: Buy when RSI crosses above 30, sell when crosses below 70
        pos = 0
        pos_list = []
        for i in range(len(rsi)):
            if rsi.iloc[i] < 30:
                pos = 1
            elif rsi.iloc[i] > 70:
                pos = 0
            pos_list.append(pos)
        signals = pd.Series(pos_list, index=df.index)
        
    res = run_backtest(df, signals)
    
    eq_strat = res['equity_curve']
    eq_bh = res['bh_equity_curve']
    metrics = res['metrics']
    bh_metrics = res['bh_metrics']
    
    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eq_strat.index, y=eq_strat.values, name='Strategy', line=dict(color='var(--accent)', width=2)))
    fig.add_trace(go.Scatter(x=eq_bh.index, y=eq_bh.values, name='Buy & Hold', line=dict(color='var(--text-muted)', width=1, dash='dash')))
    
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=20, b=0),
        height=400,
        hovermode='x unified',
        yaxis_title="Cumulative Return"
    )
    
    # Metrics
    metrics_row = dbc.Row([
        dbc.Col(StatCard("TOTAL RETURN", f"{metrics['total_return']*100:.1f}%", metrics['total_return'] - bh_metrics['total_return'], (metrics['total_return'] - bh_metrics['total_return'])*100, "bt-tot"), md=2),
        dbc.Col(StatCard("CAGR", f"{metrics['cagr']*100:.1f}%", metrics['cagr'] - bh_metrics['cagr'], (metrics['cagr'] - bh_metrics['cagr'])*100, "bt-cagr"), md=2),
        dbc.Col(StatCard("SHARPE RATIO", f"{metrics['sharpe']:.2f}", metrics['sharpe'] - bh_metrics['sharpe'], 0, "bt-sharpe"), md=2),
        dbc.Col(StatCard("MAX DRAWDOWN", f"{metrics['max_drawdown']*100:.1f}%", 0, 0, "bt-mdd"), md=2),
        dbc.Col(StatCard("WIN RATE", f"{metrics['win_rate']*100:.1f}%", 0, 0, "bt-win"), md=2),
        dbc.Col(StatCard("TRADES", int(metrics['trade_count']), 0, 0, "bt-trd"), md=2),
    ])
    
    return html.Div([
        html.Div(className="terminal-card", children=[
            html.Div("Equity Curve", className="card-title"),
            dcc.Graph(figure=fig, config={'displayModeBar': False}),
        ]),
        metrics_row
    ])
