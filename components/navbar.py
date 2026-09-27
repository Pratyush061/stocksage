from dash import html, dcc, callback, Input, Output

NAV_ITEMS = [
    ("bi bi-grid-1x2", "Overview", "/"),
    ("bi bi-graph-up-arrow", "Analysis", "/analysis"),
    ("bi bi-cpu", "AI Prediction", "/prediction"),
    ("bi bi-funnel", "Screener", "/screener"),
    ("bi bi-activity", "Backtest", "/backtest"),
]


def get_sidebar():
    return html.Div(
        [
            html.Div(
                [
                    html.Img(src="/assets/logo.svg", alt="StockSage logo",
                             style={"width": "26px", "height": "26px"}),
                    html.Div(
                        [
                            html.H5("StockSage", className="brand-text"),
                            html.Div("NSE Market Intelligence",
                                     style={"fontSize": "10px", "color": "var(--text-muted)",
                                            "marginTop": "-2px"}),
                        ],
                    ),
                ],
                className="sidebar-header",
            ),
            html.Nav(id="sidebar-nav", className="sidebar-nav"),
            html.Div(
                "Data: Yahoo Finance (delayed)<br>Built with Dash + Plotly",
                className="sidebar-footer",
            ),
        ],
        className="sidebar",
    )


@callback(Output("sidebar-nav", "children"), Input("url", "pathname"))
def render_nav(pathname):
    """Sidebar navigation with active-page highlighting."""
    links = []
    for icon, label, href in NAV_ITEMS:
        active = " active" if pathname == href else ""
        links.append(
            dcc.Link(
                [
                    html.I(className=f"bi {icon} nav-icon"),
                    html.Span(label, className="nav-text"),
                ],
                href=href,
                className=f"nav-link{active}",
            )
        )
    return links
