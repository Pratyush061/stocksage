from dash import html, dcc
import dash_bootstrap_components as dbc

def get_sidebar():
    return html.Div(
        [
            html.Div(
                [
                    html.Img(src="/assets/logo.svg", style={"width": "24px", "marginRight": "12px"}),
                    html.H5("StockSage", className="brand-text", style={"margin": "0", "fontWeight": "600", "color": "white"}),
                ],
                style={"padding": "20px", "display": "flex", "alignItems": "center", "borderBottom": "1px solid var(--border)"}
            ),
            html.Nav(
                [
                    dcc.Link([html.I(className="bi bi-grid"), html.Span("Overview", className="nav-text")], href="/", className="nav-link", id="nav-overview"),
                    dcc.Link([html.I(className="bi bi-bar-chart"), html.Span("Analysis", className="nav-text")], href="/analysis", className="nav-link", id="nav-analysis"),
                    dcc.Link([html.I(className="bi bi-cpu"), html.Span("AI Prediction", className="nav-text")], href="/prediction", className="nav-link", id="nav-prediction"),
                    dcc.Link([html.I(className="bi bi-funnel"), html.Span("Screener", className="nav-text")], href="/screener", className="nav-link", id="nav-screener"),
                    dcc.Link([html.I(className="bi bi-graph-up"), html.Span("Backtest", className="nav-text")], href="/backtest", className="nav-link", id="nav-backtest"),
                ],
                style={"paddingTop": "16px", "flex": "1"}
            ),
            html.Div(
                [
                    html.Small("Data: Yahoo Finance (delayed) · Built with Dash + Plotly", style={"color": "var(--text-muted)", "fontSize": "11px", "textAlign": "center", "display": "block", "lineHeight": "1.4"})
                ],
                style={"padding": "16px", "borderTop": "1px solid var(--border)"}
            )
        ],
        className="sidebar"
    )
