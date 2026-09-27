import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from data.market_data import get_current_price_info, get_intraday_data
from data.nifty50 import NIFTY_50
from components.stat_card import StatCard
from components.loading import StyledLoading
from components.disclaimer import Disclaimer
import pandas as pd

dash.register_page(__name__, path='/', name='Overview')

def create_sparkline(df, color):
    fig = go.Figure(go.Scatter(x=df.index, y=df['Close'], mode='lines', line=dict(color=color, width=2)))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=60,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False
    )
    return fig

layout = html.Div([
    html.Div([
        html.H2("Market Pulse — NSE", style={"margin": 0}),
        html.Div(datetime.now().strftime("%d %b %Y, %H:%M IST"), style={"color": "var(--text-muted)", "fontSize": "14px"})
    ], style={"marginBottom": "24px", "display": "flex", "justifyContent": "space-between", "alignItems": "flex-end"}),
    
    StyledLoading(html.Div(id="overview-cards")),
    
    dbc.Row([
        dbc.Col([
            html.Div(className="terminal-card", children=[
                html.Div("Nifty 50 Heatmap", className="card-title"),
                StyledLoading(dcc.Graph(id="nifty-heatmap", config={'displayModeBar': False}))
            ])
        ], md=8),
        dbc.Col([
            html.Div(className="terminal-card", children=[
                html.Div("Top Movers", className="card-title"),
                StyledLoading(html.Div(id="top-movers"))
            ])
        ], md=4)
    ]),
    Disclaimer()
])

@callback(
    Output("overview-cards", "children"),
    Input("url", "pathname")
)
def update_cards(_):
    # Try fetching Nifty and Sensex
    nifty = get_current_price_info('^NSEI')
    sensex = get_current_price_info('^BSESN')
    
    nifty_df = get_intraday_data('^NSEI')
    sensex_df = get_intraday_data('^BSESN')
    
    nifty_color = "var(--bull)" if nifty['change'] >= 0 else "var(--bear)"
    sensex_color = "var(--bull)" if sensex['change'] >= 0 else "var(--bear)"
    
    cards = dbc.Row([
        dbc.Col([
            html.Div(className="terminal-card", children=[
                StatCard("NIFTY 50", nifty['close'], nifty['change'], nifty['change_pct'], "nifty-card"),
                dcc.Graph(figure=create_sparkline(nifty_df, nifty_color) if not nifty_df.empty else go.Figure(), config={'displayModeBar': False}, style={"marginTop": "10px"})
            ])
        ], md=3),
        dbc.Col([
            html.Div(className="terminal-card", children=[
                StatCard("SENSEX", sensex['close'], sensex['change'], sensex['change_pct'], "sensex-card"),
                dcc.Graph(figure=create_sparkline(sensex_df, sensex_color) if not sensex_df.empty else go.Figure(), config={'displayModeBar': False}, style={"marginTop": "10px"})
            ])
        ], md=3),
    ])
    
    return cards

@callback(
    Output("nifty-heatmap", "figure"),
    Output("top-movers", "children"),
    Input("url", "pathname")
)
def update_heatmap(_):
    data = []
    for stock in NIFTY_50:
        info = get_current_price_info(stock['symbol'])
        data.append({
            'Symbol': stock['symbol'].replace('.NS', ''),
            'Name': stock['name'],
            'Sector': stock['sector'],
            'Change': info['change_pct'],
            'Volume': info['volume'],
            'Price': info['close']
        })
        
    df = pd.DataFrame(data)
    df['MarketCapProxy'] = df['Price'] * df['Volume']
    df = df[df['MarketCapProxy'] > 0]
    
    if df.empty:
        return go.Figure(), html.Div("No data available")
    
    fig = px.treemap(
        df, 
        path=[px.Constant("Nifty 50"), 'Sector', 'Symbol'], 
        values='MarketCapProxy',
        color='Change',
        color_continuous_scale=[(0, "var(--bear)"), (0.5, "#1A2336"), (1, "var(--bull)")],
        color_continuous_midpoint=0,
        custom_data=['Change']
    )
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Change: %{customdata[0]:.2f}%<extra></extra>',
        texttemplate='<b>%{label}</b><br>%{customdata[0]:.2f}%',
        textfont_family="Inter", textfont_color="white"
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_showscale=False
    )
    
    top_gainers = df.nlargest(3, 'Change')
    top_losers = df.nsmallest(3, 'Change')
    
    def mover_row(row, is_gainer):
        color = "text-bull" if is_gainer else "text-bear"
        icon = "bi bi-caret-up-fill" if is_gainer else "bi bi-caret-down-fill"
        return html.Div([
            html.Div(row['Symbol'], style={"fontWeight": "600", "width": "60px"}),
            html.Div(f"₹{row['Price']:.2f}", className="tabular-nums", style={"flex": 1}),
            html.Div([html.I(className=icon), f" {abs(row['Change']):.2f}%"], className=f"{color} tabular-nums")
        ], style={"display": "flex", "justifyContent": "space-between", "padding": "12px 0", "borderBottom": "1px solid var(--border)"})
    
    movers = html.Div([
        html.Div("Top Gainers", style={"fontSize": "12px", "color": "var(--text-muted)", "marginBottom": "8px"}),
        html.Div([mover_row(r, True) for _, r in top_gainers.iterrows()]),
        html.Div("Top Losers", style={"fontSize": "12px", "color": "var(--text-muted)", "marginBottom": "8px", "marginTop": "16px"}),
        html.Div([mover_row(r, False) for _, r in top_losers.iterrows()])
    ])
    
    return fig, movers
