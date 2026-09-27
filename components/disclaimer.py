from dash import html


def Disclaimer():
    return html.Div(
        "Educational & research use only — not investment advice. "
        "Market data is delayed; forecasts are statistical estimates, not guarantees.",
        className="disclaimer",
    )
