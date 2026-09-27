import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd

import theme
from data.market_data import get_batch_price_info, get_intraday_data
from data.nifty50 import NIFTY_50
from components.stat_card import StatCard
from components.loading import StyledLoading
from components.disclaimer import Disclaimer

dash.register_page(__name__, path='/', name='Overview')

SYMBOLS = [stock['symbol'] for stock in NIFTY_50]


def create_sparkline(df, color):
    fig = go.Figure(
        go.Scatter(
            x=df.index, y=df['Close'], mode='lines',
            line=dict(color=color, width=1.8),
            fill='tozeroy',
            fillcolor=theme.hex_to_rgba(color, 0.12),
        )
    )
    fig.update_layout(**theme.sparkline_layout(), height=52)
    return fig


layout = html.Div([
    html.Div([
        html.Div([
            html.H2("Market Pulse — NSE", className="page-title"),
            html.Div(datetime.now().strftime("%d %b %Y · %H:%M IST"), className="page-subtitle"),
        ]),
        dbc.Badge("LIVE · delayed 15m", color="secondary", pill=True,
                  style={"fontSize": "11px", "alignSelf": "center"}),
    ], className="page-header"),

    StyledLoading(html.Div(id="overview-cards")),

    dbc.Row([
        dbc.Col([
            html.Div(className="terminal-card", children=[
                html.Div("Nifty 50 Heatmap", className="card-title"),
                StyledLoading(dcc.Graph(id="nifty-heatmap", config={'displayModeBar': False},
                                        style={"height": "480px"})),
            ])
        ], lg=8, md=12, className="mb-3"),
        dbc.Col([
            html.Div(className="terminal-card", children=[
                html.Div("Top Movers", className="card-title"),
                StyledLoading(html.Div(id="top-movers")),
            ])
        ], lg=4, md=12, className="mb-3"),
    ]),

    dbc.Row([
        dbc.Col([
            html.Div(className="terminal-card", children=[
                html.Div("Sector Performance · 1D", className="card-title"),
                StyledLoading(dcc.Graph(id="sector-performance", config={'displayModeBar': False},
                                        style={"height": "380px"})),
            ])
        ], md=12),
    ]),

    Disclaimer(),
])


@callback(
    Output("overview-cards", "children"),
    Input("url", "pathname"),
)
def update_cards(_):
    # ONE batched call for both indices instead of 4 sequential fetches
    idx = get_batch_price_info(['^NSEI', '^BSESN'])
    nifty, sensex = idx['^NSEI'], idx['^BSESN']

    nifty_df = get_intraday_data('^NSEI')
    sensex_df = get_intraday_data('^BSESN')

    def _card(sym, info, intraday, label):
        color = theme.BULL if info['change'] >= 0 else theme.BEAR
        children = [StatCard(label, info['close'], info['change'], info['change_pct'], sym)]
        if intraday is not None and not intraday.empty:
            children.append(dcc.Graph(
                figure=create_sparkline(intraday, color),
                config={'displayModeBar': False},
            ))
        return children

    return dbc.Row([
        dbc.Col(html.Div(className="terminal-card", children=_card("nifty", nifty, nifty_df, "NIFTY 50")), md=6, lg=3, className="mb-3"),
        dbc.Col(html.Div(className="terminal-card", children=_card("sensex", sensex, sensex_df, "SENSEX")), md=6, lg=3, className="mb-3"),
    ])


@callback(
    Output("nifty-heatmap", "figure"),
    Output("top-movers", "children"),
    Output("sector-performance", "figure"),
    Input("url", "pathname"),
)
def update_market(_):
    # ONE batched call for all 50 Nifty constituents (was: 50 serial requests)
    quotes = get_batch_price_info(SYMBOLS)
    data = []
    for stock in NIFTY_50:
        q = quotes.get(stock['symbol'], {"close": 0, "change_pct": 0, "volume": 0})
        if q['close'] <= 0:
            continue
        data.append({
            'Symbol': stock['symbol'].replace('.NS', ''),
            'Name': stock['name'],
            'Sector': stock['sector'],
            'Change': q['change_pct'],
            'Volume': q['volume'],
            'Price': q['close'],
        })

    df = pd.DataFrame(data)
    if df.empty:
        empty = go.Figure()
        theme.apply_theme(empty)
        return empty, html.Div("Market data unavailable — please retry."), empty

    df['MarketCapProxy'] = df['Price'] * df['Volume']
    df = df[df['MarketCapProxy'] > 0]

    # ---- Heatmap ----
    fig = px.treemap(
        df,
        path=[px.Constant("Nifty 50"), 'Sector', 'Symbol'],
        values='MarketCapProxy',
        color='Change',
        color_continuous_scale=theme.HEATMAP_SCALE,
        color_continuous_midpoint=0,
        custom_data=['Change'],
    )
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Change: %{customdata[0]:.2f}%<extra></extra>',
        texttemplate='<b>%{label}</b><br>%{customdata[0]:.2f}%',
        textfont=dict(family=theme.FONT_FAMILY, size=12),
        marker=dict(line=dict(color=theme.BG, width=2)),
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_showscale=False,
        font=dict(family=theme.FONT_FAMILY, color=theme.TEXT),
    )

    # ---- Top movers ----
    top_gainers = df.nlargest(5, 'Change')
    top_losers = df.nsmallest(5, 'Change')

    def mover_row(row, is_gainer):
        color = "text-bull" if is_gainer else "text-bear"
        icon = "bi bi-caret-up-fill" if is_gainer else "bi bi-caret-down-fill"
        return html.Div([
            html.Div(row['Symbol'], className="mover-symbol"),
            html.Div(f"₹{row['Price']:,.2f}", className="mover-price num"),
            html.Div([html.I(className=icon), f" {abs(row['Change']):.2f}%"],
                     className=f"{color} num mover-change"),
        ], className="mover-row")

    movers = html.Div([
        html.Div("GAINERS", className="stat-card-label"),
        *[mover_row(r, True) for _, r in top_gainers.iterrows()],
        html.Div("LOSERS", className="stat-card-label", style={"marginTop": "16px"}),
        *[mover_row(r, False) for _, r in top_losers.iterrows()],
    ])

    # ---- Sector performance ----
    sector = df.groupby('Sector', as_index=False)['Change'].median().sort_values('Change')
    colors = [theme.BULL if v >= 0 else theme.BEAR for v in sector['Change']]
    sfig = go.Figure(go.Bar(
        x=sector['Change'],
        y=sector['Sector'],
        orientation='h',
        marker_color=colors,
        hovertemplate='<b>%{y}</b><br>Median change: %{x:.2f}%<extra></extra>',
    ))
    theme.apply_theme(sfig, x_grid=True, y_grid=False)
    sfig.update_layout(margin=dict(l=8, r=16, t=8, b=8), height=380, showlegend=False)

    return fig, movers, sfig
