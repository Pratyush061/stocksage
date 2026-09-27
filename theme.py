"""
StockSage design system — Python side.

Single source of truth for colors used in Plotly figures and any
server-rendered styling. Keep in sync with assets/styles.css tokens.
Plotly cannot resolve CSS variables, so always use these constants
when building figures.
"""

# --- Palette (TradingView-inspired dark terminal) ---
BG = "#131722"           # page background
PANEL = "#1E222D"        # card / panel surface
PANEL_2 = "#2A2E39"      # elevated surface (hover, table headers)
BORDER = "#363A45"       # hairline borders
TEXT = "#D1D4DC"         # primary text
MUTED = "#787B86"        # secondary text
ACCENT = "#2962FF"       # interactive blue (links, active states)
BULL = "#089981"         # gains / up candles
BEAR = "#F23645"         # losses / down candles
WARN = "#FF9800"         # warnings
GRID = "rgba(120, 123, 134, 0.12)"   # chart gridlines
BAND_FILL = "rgba(41, 98, 255, 0.10)"  # prediction band fill
SMA_FAST = "#2962FF"     # SMA 20
SMA_SLOW = "#7E57C2"    # SMA 50
BOLLINGER = "#787B86"
PREDICTION = "#FF9800"

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

# Heatmap diverging scale (bear -> neutral -> bull)
HEATMAP_SCALE = [
    (0.0, BEAR),
    (0.35, "#5A2A33"),
    (0.5, "#2A2E39"),
    (0.65, "#1D5C4F"),
    (1.0, BULL),
]


def apply_theme(fig, x_grid=True, y_grid=True, hover_bg=None, hover_border=None):
    """Apply the StockSage dark chart template to a Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=12, color=TEXT),
        margin=dict(l=8, r=16, t=36, b=8),
        hoverlabel=dict(
            bgcolor=hover_bg or "#2A2E39",
            bordercolor=hover_border or BORDER,
            font=dict(family=FONT_FAMILY, size=12, color=TEXT),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=MUTED),
            orientation="h",
            yanchor="bottom",
            y=1.02,
        ),
        xaxis=dict(
            showgrid=x_grid,
            gridcolor=GRID,
            zeroline=False,
            linecolor=BORDER,
            ticksuffix=" ",
            tickfont=dict(color=MUTED, size=11),
        ),
        yaxis=dict(
            showgrid=y_grid,
            gridcolor=GRID,
            zeroline=False,
            tickfont=dict(color=MUTED, size=11),
        ),
    )
    return fig


def hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    """Convert '#RRGGBB' to 'rgba(r, g, b, alpha)'."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def sparkline_layout():
    """Minimal layout for tiny sparkline figures."""
    return dict(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        showlegend=False,
        hovermode=False,
    )
