import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

import theme
from data.market_data import get_daily_history, get_current_price_info
from data.nifty50 import NIFTY_50
from analytics.indicators import compute_sma, compute_rsi, compute_macd, compute_bollinger_bands
from components.loading import StyledLoading
from components.stat_card import StatCard
from components.disclaimer import Disclaimer

dash.register_page(__name__, path='/analysis', name='Analysis')

stock_options = [{"label": f"{s['symbol'].replace('.NS', '')} · {s['name']}", "value": s['symbol']} for s in NIFTY_50]

layout = html.Div([
    html.Div([
        html.Div([
            html.H2("Stock Analysis", className="page-title"),
            html.Div("Candlesticks, technical indicators and volume — pick any NSE stock.", className="page-subtitle"),
        ]),
    ], className="page-header"),

    html.Div(className="terminal-card", children=[
        dbc.Row([
            dbc.Col([
                html.Div("STOCK", className="stat-card-label"),
                dcc.Dropdown(
                    id="analysis-stock-dropdown",
                    options=stock_options,
                    value="RELIANCE.NS",
                    placeholder="Search — try RELIANCE, TCS, HDFC Bank…",
                ),
            ], lg=4, md=12, className="mb-2"),
            dbc.Col([
                html.Div("PERIOD", className="stat-card-label"),
                dbc.RadioItems(
                    id="analysis-period",
                    options=[
                        {"label": " 1M ", "value": "1mo"},
                        {"label": " 3M ", "value": "3mo"},
                        {"label": " 6M ", "value": "6mo"},
                        {"label": " 1Y ", "value": "1y"},
                        {"label": " 5Y ", "value": "5y"},
                    ],
                    value="1y",
                    inline=True,
                    className="control-group",
                    inputClassName="d-none",
                    labelClassName="control-item",
                    labelCheckedClassName="active",
                ),
            ], lg=4, md=12, className="mb-2"),
            dbc.Col([
                html.Div("OVERLAYS", className="stat-card-label"),
                dbc.Checklist(
                    options=[
                        {"label": " SMA 20/50 ", "value": "sma"},
                        {"label": " Bollinger Bands ", "value": "bb"},
                    ],
                    value=["sma"],
                    id="analysis-toggles",
                    inline=True,
                    switch=True,
                ),
            ], lg=4, md=12, className="mb-2"),
        ]),
    ], style={"marginBottom": "24px"}),

    StyledLoading(html.Div(id="analysis-stats", style={"marginBottom": "24px"})),

    html.Div(className="terminal-card", children=[
        StyledLoading(dcc.Graph(id="analysis-chart", style={"height": "780px"}, config={'displayModeBar': False}))
    ]),

    Disclaimer(),
])


@callback(
    Output("analysis-stats", "children"),
    Output("analysis-chart", "figure"),
    Input("analysis-stock-dropdown", "value"),
    Input("analysis-period", "value"),
    Input("analysis-toggles", "value"),
)
def update_analysis(symbol, period, toggles):
    if not symbol:
        return html.Div(), go.Figure()

    df = get_daily_history(symbol, period=period)
    info = get_current_price_info(symbol)

    if df.empty:
        return html.Div("No data found — check the symbol.", className="text-bear"), go.Figure()

    # ---------- Stats ----------
    last_close = info['close'] or float(df['Close'].iloc[-1])
    day_change = info['change']
    change_pct = info['change_pct']

    high52 = df['High'].tail(252).max()
    low52 = df['Low'].tail(252).min()
    daily_ret = df['Close'].pct_change()
    vol30 = daily_ret.tail(30).std() * (252 ** 0.5) * 100
    avg_vol = df['Volume'].tail(20).mean()
    current_rsi = float(compute_rsi(df['Close']).iloc[-1])

    stats_row = dbc.Row([
        dbc.Col(StatCard("LAST CLOSE", last_close, day_change, change_pct, "ana-close"), md=4, lg=2, className="mb-3"),
        dbc.Col(StatCard("52W HIGH", high52, 0, 0, "ana-h52"), md=4, lg=2, className="mb-3"),
        dbc.Col(StatCard("52W LOW", low52, 0, 0, "ana-l52"), md=4, lg=2, className="mb-3"),
        dbc.Col(StatCard("30D VOLATILITY", vol30, 0, 0, "ana-vol", subtitle="annualized"), md=4, lg=2, className="mb-3"),
        dbc.Col(StatCard("AVG VOLUME", avg_vol / 1e6, 0, 0, "ana-avgvol", subtitle="20-day, millions"), md=4, lg=2, className="mb-3"),
        dbc.Col(StatCard("RSI (14)", current_rsi, 0, 0, "ana-rsi", subtitle="overbought > 70"), md=4, lg=2, className="mb-3"),
    ])

    # ---------- Chart ----------
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.025,
        row_width=[0.16, 0.16, 0.14, 0.62],
        subplot_titles=("Price", "Volume", "RSI (14)", "MACD (12, 26, 9)"),
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='Price',
        increasing_line_color=theme.BULL, decreasing_line_color=theme.BEAR,
        increasing_fillcolor=theme.BULL, decreasing_fillcolor=theme.BEAR,
    ), row=1, col=1)

    if "sma" in toggles:
        fig.add_trace(go.Scatter(x=df.index, y=compute_sma(df['Close'], 20), mode='lines',
                                 name='SMA 20', line=dict(color=theme.SMA_FAST, width=1.4)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=compute_sma(df['Close'], 50), mode='lines',
                                 name='SMA 50', line=dict(color=theme.SMA_SLOW, width=1.4)), row=1, col=1)

    if "bb" in toggles:
        upper, mid, lower = compute_bollinger_bands(df['Close'])
        fig.add_trace(go.Scatter(x=df.index, y=upper, mode='lines', name='BB Upper',
                                 line=dict(color=theme.BOLLINGER, dash='dash', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lower, mode='lines', name='BB Lower',
                                 line=dict(color=theme.BOLLINGER, dash='dash', width=1),
                                 fill='tonexty', fillcolor=theme.hex_to_rgba(theme.BOLLINGER, 0.08)), row=1, col=1)

    # Volume
    vol_colors = [theme.BULL if c >= o else theme.BEAR for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume',
                         marker_color=vol_colors, marker_line=dict(width=0)), row=2, col=1)

    # RSI
    rsi = compute_rsi(df['Close'])
    fig.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI', line=dict(color=theme.ACCENT, width=1.4)), row=3, col=1)
    fig.add_hline(y=70, line_dash='dot', line_color=theme.BEAR, line_width=0.8, row=3, col=1)
    fig.add_hline(y=30, line_dash='dot', line_color=theme.BULL, line_width=0.8, row=3, col=1)

    # MACD
    macd_line, sig_line, macd_hist = compute_macd(df['Close'])
    fig.add_trace(go.Bar(x=df.index, y=macd_hist, name='Histogram',
                         marker_color=[theme.hex_to_rgba(theme.BULL, 0.55) if v > 0 else theme.hex_to_rgba(theme.BEAR, 0.55) for v in macd_hist],
                         marker_line=dict(width=0)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=macd_line, name='MACD', line=dict(color=theme.ACCENT, width=1.4)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=sig_line, name='Signal', line=dict(color=theme.WARN, width=1.2)), row=4, col=1)

    # Layout
    theme.apply_theme(fig)
    fig.update_layout(
        margin=dict(l=8, r=8, t=20, b=8),
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        bargap=0,
    )
    fig.update_xaxes(showspikes=True, spikemode="across", spikedistance=-1,
                     spikelinedict=dict(color=theme.MUTED, thickness=0.7, dash='dot'))
    for ax in fig.select_yaxes():
        ax.update(showgrid=True, gridcolor=theme.GRID, zeroline=False)
    for ax in fig.select_xaxes():
        ax.update(showgrid=False, linecolor=theme.BORDER)
    # subtitle styling
    fig.update_annotations(font=dict(family=theme.FONT_FAMILY, size=11, color=theme.MUTED))

    return stats_row, fig
