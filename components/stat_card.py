from dash import html
import dash_bootstrap_components as dbc

def StatCard(title, value, delta, delta_text, id_prefix):
    delta_color = "text-bull" if delta > 0 else "text-bear" if delta < 0 else "text-muted"
    delta_icon = "bi bi-arrow-up-right" if delta > 0 else "bi bi-arrow-down-right" if delta < 0 else "bi bi-dash"
    
    return html.Div(
        [
            html.Div(title, className="card-title"),
            html.Div(
                [
                    html.Div(f"{value:,.2f}" if isinstance(value, (int, float)) else value, className="stat-value tabular-nums", id=f"{id_prefix}-value"),
                    html.Div(
                        [
                            html.I(className=delta_icon),
                            html.Span(f"{abs(delta_text):.2f}%" if isinstance(delta_text, (int, float)) else delta_text)
                        ],
                        className=f"stat-delta {delta_color} tabular-nums",
                        id=f"{id_prefix}-delta"
                    )
                ],
                style={"display": "flex", "alignItems": "baseline", "justifyContent": "space-between"}
            )
        ],
        className="terminal-card",
        id=f"{id_prefix}-card"
    )
