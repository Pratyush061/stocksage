import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from data.market_data import get_daily_history
from data.nifty50 import NIFTY_50
from analytics.indicators import compute_rsi, compute_sma, compute_bollinger_bands
from components.loading import StyledLoading
from components.disclaimer import Disclaimer

dash.register_page(__name__, path='/screener', name='Screener')

layout = html.Div([
    html.H2("Quantitative Screener", style={"marginBottom": "24px"}),
    
    dbc.Row([
        dbc.Col([
            html.Div("RSI Filter", className="card-title"),
            dbc.Select(
                id="screen-rsi",
                options=[
                    {"label": "Any", "value": "any"},
                    {"label": "Oversold (< 30)", "value": "oversold"},
                    {"label": "Overbought (> 70)", "value": "overbought"},
                ],
                value="any"
            )
        ], md=3),
        dbc.Col([
            html.Div("Trend Filter", className="card-title"),
            dbc.Select(
                id="screen-trend",
                options=[
                    {"label": "Any", "value": "any"},
                    {"label": "Above SMA 50", "value": "above"},
                    {"label": "Below SMA 50", "value": "below"},
                ],
                value="any"
            )
        ], md=3),
        dbc.Col([
            html.Div("Volume Surge", className="card-title"),
            dbc.Select(
                id="screen-vol",
                options=[
                    {"label": "Any", "value": "any"},
                    {"label": "> 1.5x 20d Avg", "value": "surge"},
                ],
                value="any"
            )
        ], md=3),
        dbc.Col([
            html.Div(style={"height": "25px"}),
            dbc.Button("Run Screen", id="run-screen", color="primary", className="w-100", style={"backgroundColor": "var(--accent)", "border": "none", "color": "var(--bg)", "fontWeight": "600"})
        ], md=3)
    ], style={"marginBottom": "24px"}),
    
    html.Div(className="terminal-card", children=[
        StyledLoading(html.Div(id="screener-table-container"))
    ]),
    
    Disclaimer()
])

@callback(
    Output("screener-table-container", "children"),
    Input("run-screen", "n_clicks"),
    State("screen-rsi", "value"),
    State("screen-trend", "value"),
    State("screen-vol", "value"),
)
def update_screener(n_clicks, rsi_f, trend_f, vol_f):
    results = []
    
    # In a real app, you'd calculate these in batch or query a pre-computed DB.
    # We loop for demonstration (cached so it's relatively fast after first run)
    for stock in NIFTY_50:
        symbol = stock['symbol']
        df = get_daily_history(symbol, period="6mo")
        if df.empty or len(df) < 55:
            continue
            
        close = df['Close']
        vol = df['Volume']
        
        current_close = close.iloc[-1]
        
        rsi = compute_rsi(close).iloc[-1]
        sma50 = compute_sma(close, 50).iloc[-1]
        vol20 = compute_sma(vol, 20).iloc[-1]
        
        current_vol = vol.iloc[-1]
        
        # Momentum (5-day return)
        mom5 = (current_close / close.iloc[-6]) - 1
        
        # Bollinger
        upper, mid, lower = compute_bollinger_bands(close)
        pb = (current_close - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1] + 1e-8)
        
        # Filters
        if rsi_f == "oversold" and rsi >= 30: continue
        if rsi_f == "overbought" and rsi <= 70: continue
        
        if trend_f == "above" and current_close <= sma50: continue
        if trend_f == "below" and current_close >= sma50: continue
        
        if vol_f == "surge" and current_vol <= (1.5 * vol20): continue
        
        results.append({
            "Symbol": symbol.replace('.NS', ''),
            "Name": stock['name'],
            "Price": round(current_close, 2),
            "RSI": round(rsi, 2),
            "SMA50 Dist %": round(((current_close / sma50) - 1) * 100, 2),
            "Vol Ratio": round(current_vol / vol20, 2),
            "5d Mom %": round(mom5 * 100, 2),
            "BB %B": round(pb, 2)
        })
        
    if not results:
        return html.Div("No stocks match the given criteria.", className="text-muted", style={"padding": "20px", "textAlign": "center"})
        
    df_res = pd.DataFrame(results)
    
    return dash_table.DataTable(
        data=df_res.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_res.columns],
        sort_action="native",
        page_action="native",
        page_current=0,
        page_size=15,
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': 'var(--surface)',
            'color': 'var(--text)',
            'border': 'none',
            'borderBottom': '1px solid var(--border)',
            'padding': '12px',
            'fontFamily': 'Space Grotesk, sans-serif',
            'fontSize': '13px',
            'textAlign': 'left'
        },
        style_header={
            'backgroundColor': 'var(--surface-2)',
            'color': 'var(--text-muted)',
            'fontWeight': '600',
            'border': 'none',
            'borderBottom': '1px solid var(--border)',
            'fontFamily': 'Inter, sans-serif',
            'fontSize': '12px',
            'textTransform': 'uppercase'
        },
        style_data_conditional=[
            {
                'if': {'state': 'active'},
                'backgroundColor': 'var(--surface-2)',
                'border': '1px solid var(--accent)'
            }
        ]
    )
