import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from data.market_data import get_daily_history, get_current_price_info
from data.nifty50 import NIFTY_50
from analytics.indicators import compute_sma, compute_rsi, compute_macd, compute_bollinger_bands
from components.loading import StyledLoading
from components.stat_card import StatCard
from components.disclaimer import Disclaimer

dash.register_page(__name__, path='/analysis', name='Analysis')

stock_options = [{"label": f"{s['symbol']} - {s['name']}", "value": s['symbol']} for s in NIFTY_50]

layout = html.Div([
    html.H2("Stock Analysis", style={"marginBottom": "24px"}),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id="analysis-stock-dropdown",
                options=stock_options,
                placeholder="Search a stock to begin — try RELIANCE.NS, TCS.NS, or HDFCBANK.NS.",
                className="dark-dropdown"
            )
        ], md=4),
        dbc.Col([
            dbc.RadioItems(
                id="analysis-period",
                options=[
                    {"label": "1M", "value": "1mo"},
                    {"label": "3M", "value": "3mo"},
                    {"label": "6M", "value": "6mo"},
                    {"label": "1Y", "value": "1y"},
                    {"label": "5Y", "value": "5y"},
                ],
                value="1y",
                inline=True,
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary",
                labelCheckedClassName="active",
            )
        ], md=4),
        dbc.Col([
            dbc.Checklist(
                options=[
                    {"label": "SMA 20/50", "value": "sma"},
                    {"label": "Bollinger Bands", "value": "bb"},
                ],
                value=["sma"],
                id="analysis-toggles",
                inline=True,
                switch=True,
            )
        ], md=4)
    ], style={"marginBottom": "24px"}),
    
    StyledLoading(html.Div(id="analysis-stats", style={"marginBottom": "24px"})),
    
    html.Div(className="terminal-card", children=[
        StyledLoading(dcc.Graph(id="analysis-chart", style={"height": "800px"}, config={'displayModeBar': False}))
    ]),
    
    Disclaimer()
])

@callback(
    Output("analysis-stats", "children"),
    Output("analysis-chart", "figure"),
    Input("analysis-stock-dropdown", "value"),
    Input("analysis-period", "value"),
    Input("analysis-toggles", "value")
)
def update_analysis(symbol, period, toggles):
    if not symbol:
        return html.Div(), go.Figure()
        
    df = get_daily_history(symbol, period=period)
    info = get_current_price_info(symbol)
    
    if df.empty:
        return html.Div("No data found.", className="text-bear"), go.Figure()
        
    # Stats
    last_close = info['close']
    day_change = info['change']
    change_pct = info['change_pct']
    
    high52 = df['High'].tail(252).max() if len(df) > 252 else df['High'].max()
    low52 = df['Low'].tail(252).min() if len(df) > 252 else df['Low'].min()
    
    daily_ret = df['Close'].pct_change()
    vol30 = daily_ret.tail(30).std() * (252 ** 0.5) * 100 # Annualized
    
    avg_vol = df['Volume'].tail(20).mean()
    current_rsi = compute_rsi(df['Close']).iloc[-1]
    
    stats_row = dbc.Row([
        dbc.Col(StatCard("LAST CLOSE", last_close, day_change, change_pct, "ana-close"), md=2),
        dbc.Col(StatCard("52W HIGH", high52, 0, 0, "ana-h52"), md=2),
        dbc.Col(StatCard("52W LOW", low52, 0, 0, "ana-l52"), md=2),
        dbc.Col(StatCard("30D VOLATILITY", f"{vol30:.1f}%", 0, 0, "ana-vol"), md=2),
        dbc.Col(StatCard("AVG VOLUME", f"{avg_vol/1e6:.1f}M", 0, 0, "ana-avgvol"), md=2),
        dbc.Col(StatCard("RSI (14)", current_rsi, 0, 0, "ana-rsi"), md=2),
    ])
    
    # Chart
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=(symbol, 'Volume', 'RSI & MACD'),
                        row_width=[0.2, 0.2, 0.6])
                        
    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price', increasing_line_color='var(--bull)', decreasing_line_color='var(--bear)'), row=1, col=1)
    
    if "sma" in toggles:
        fig.add_trace(go.Scatter(x=df.index, y=compute_sma(df['Close'], 20), mode='lines', name='SMA 20', line=dict(color='var(--accent)')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=compute_sma(df['Close'], 50), mode='lines', name='SMA 50', line=dict(color='#818CF8')), row=1, col=1)
        
    if "bb" in toggles:
        upper, mid, lower = compute_bollinger_bands(df['Close'])
        fig.add_trace(go.Scatter(x=df.index, y=upper, mode='lines', name='BB Upper', line=dict(color='#475569', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lower, mode='lines', name='BB Lower', line=dict(color='#475569', dash='dash'), fill='tonexty', fillcolor='rgba(71,85,105,0.1)'), row=1, col=1)
        
    # Volume
    colors = ['var(--bull)' if c >= o else 'var(--bear)' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors), row=2, col=1)
    
    # Indicators
    fig.add_trace(go.Scatter(x=df.index, y=compute_rsi(df['Close']), name='RSI', line=dict(color='var(--accent)')), row=3, col=1)
    macd_line, sig_line, macd_hist = compute_macd(df['Close'])
    fig.add_trace(go.Bar(x=df.index, y=macd_hist, name='MACD Hist', marker_color=['var(--bull)' if v > 0 else 'var(--bear)' for v in macd_hist]), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=macd_line, name='MACD', line=dict(color='#818CF8')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=sig_line, name='Signal', line=dict(color='#F59E0B')), row=3, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        spikedistance=-1,
    )
    
    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor", showline=False, showgrid=True, gridcolor="rgba(148,163,184,0.08)")
    fig.update_yaxes(showspikes=True, spikemode="across", spikesnap="cursor", showline=False, showgrid=True, gridcolor="rgba(148,163,184,0.08)")
    
    return stats_row, fig
