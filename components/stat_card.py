from dash import html


def StatCard(title, value, delta, delta_pct, id_prefix, subtitle=None):
    """Market stat card: label, big tabular number, delta chip, optional subtitle."""
    direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
    delta_icon = {
        "up": "bi bi-caret-up-fill",
        "down": "bi bi-caret-down-fill",
        "flat": "bi bi-dash-lg",
    }[direction]

    return html.Div(
        [
            html.Div(title, className="stat-card-label"),
            html.Div(
                f"{value:,.2f}" if isinstance(value, (int, float)) else str(value),
                className="stat-card-value num",
            ),
            html.Div(
                [
                    html.I(className=delta_icon),
                    html.Span(f"{delta:+,.2f} ({delta_pct:+.2f}%)"),
                ],
                className=f"stat-card-delta {direction} num",
            ),
            html.Div(subtitle, className="stat-card-sub") if subtitle else None,
        ],
        className="terminal-card",
        id=f"{id_prefix}-card",
    )
