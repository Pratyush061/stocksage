from dash import Dash, html, dcc, page_container, DiskcacheManager
import dash_bootstrap_components as dbc
from components.navbar import get_sidebar
from data.market_data import init_cache
import diskcache

cache_dir = "background_callback_cache"
background_callback_manager = DiskcacheManager(diskcache.Cache(cache_dir))

app = Dash(
    __name__,
    use_pages=True,
    # Neutral bootstrap base for the grid system only — all visual styling
    # lives in assets/styles.css (see theme.py for the Python-side palette).
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    title="StockSage India — NSE Market Intelligence",
    suppress_callback_exceptions=True,
    background_callback_manager=background_callback_manager,
)

init_cache(app)

# Expose the underlying Flask server for gunicorn (see Procfile / Dockerfile)
server = app.server

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        get_sidebar(),
        html.Div(
            page_container,
            className="content",
        ),
    ],
    className="app-container",
)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
