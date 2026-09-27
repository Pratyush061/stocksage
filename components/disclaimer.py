from dash import html

def Disclaimer():
    return html.Div(
        "Educational & research use only — not investment advice. Market data is delayed; forecasts are statistical estimates, not guarantees.",
        style={
            "fontSize": "11px",
            "color": "var(--text-muted)",
            "textAlign": "center",
            "marginTop": "24px",
            "padding": "16px",
            "borderTop": "1px solid var(--border)"
        }
    )
