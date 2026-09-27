import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import plotly.express as px

import theme
from data.market_data import get_daily_history
from data.nifty50 import NIFTY_50
from analytics.models import get_predictions
from components.loading import StyledLoading
from components.stat_card import StatCard
from components.disclaimer import Disclaimer

dash.register_page(__name__, path='/prediction', name='AI Prediction')

stock_options = [{"label": f"{s['symbol']} - {s['name']}", "value": s['symbol']} for s in NIFTY_50]

layout = html.Div([
    html.H2("AI Price Prediction", style={"marginBottom": "8px"}),
    html.P("Model forecasts are statistical estimates trained on historical prices and technical indicators. They do not account for news, earnings surprises, or regulatory events.", style={"color": "var(--text-muted)", "marginBottom": "24px", "fontSize": "14px"}),
    
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id="pred-stock",
                options=stock_options,
                placeholder="Select a stock",
                className="dark-dropdown"
            )
        ], md=4),
        dbc.Col([
            dbc.Select(
                id="pred-model",
                options=[
                    {"label": "XGBoost (Walk-Forward)", "value": "XGBoost"},
                    {"label": "LSTM (Deep Learning)", "value": "LSTM"},
                    {"label": "Ensemble (Hybrid)", "value": "Ensemble"},
                ],
                value="XGBoost"
            )
        ], md=4),
        dbc.Col([
            dbc.Select(
                id="pred-horizon",
                options=[
                    {"label": "5 Days Ahead", "value": "5"},
                    {"label": "10 Days Ahead", "value": "10"},
                    {"label": "21 Days Ahead", "value": "21"},
                ],
                value="5"
            )
        ], md=4),
    ], style={"marginBottom": "24px"}),
    
    StyledLoading(html.Div(id="pred-results")),
    
    Disclaimer()
])

@callback(
    Output("pred-results", "children"),
    Input("pred-stock", "value"),
    Input("pred-model", "value"),
    Input("pred-horizon", "value")
)
def run_prediction(symbol, model_name, horizon):
    if not symbol:
        return html.Div()
        
    horizon = int(horizon)
    df = get_daily_history(symbol, period="5y")
    
    if df.empty:
        return html.Div("No data available.", className="text-bear")
        
    # Get predictions (this is cached inside)
    res = get_predictions(df, model_name, horizon)
    
    if res is None:
        return html.Div("Not enough data to train model.", className="text-bear")
        
    # Plotting
    # We want to plot the last 100 days of actual, plus the predictions over them
    # And then a point for the future forecast.
    
    plot_df = df.tail(150).copy()
    preds = res['full_preds'].reindex(plot_df.index)
    
    # Calculate price equivalent of predictions since target is log return
    # Log return pred = log(Close_t+h / Close_t)
    # Close_t+h = Close_t * exp(pred)
    
    pred_prices = plot_df['Close'] * np.exp(preds)
    
    last_close = plot_df['Close'].iloc[-1]
    fc_price = last_close * np.exp(res['forecast'])
    fc_lower = last_close * np.exp(res['forecast_lower'])
    fc_upper = last_close * np.exp(res['forecast_upper'])
    
    # Create future dates
    last_date = plot_df.index[-1]
    future_dates = pd.bdate_range(start=last_date, periods=horizon+1)[1:]
    target_date = future_dates[-1]
    
    fig = go.Figure()
    
    # Historical
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['Close'], name='Actual Price', line=dict(color=theme.TEXT, width=2)))

    # Model Fit
    fig.add_trace(go.Scatter(x=plot_df.index, y=pred_prices, name='Model Fit', line=dict(color=theme.ACCENT, dash='dash', width=1)))

    # Forecast point and band
    fig.add_trace(go.Scatter(x=[last_date, target_date], y=[last_close, fc_price], name='Forecast', line=dict(color=theme.PREDICTION, width=2, dash='dot')))
    fig.add_trace(go.Scatter(x=[target_date], y=[fc_price], mode='markers', name='Target', marker=dict(color=theme.PREDICTION, size=9, line=dict(color=theme.BG, width=2))))

    # Confidence Band
    fig.add_trace(go.Scatter(
        x=[last_date, target_date, target_date, last_date],
        y=[last_close, fc_upper, fc_lower, last_close],
        fill='toself',
        fillcolor=theme.hex_to_rgba(theme.PREDICTION, 0.12),
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=False,
        name='80% Confidence'
    ))

    fig.add_vline(x=last_date, line_width=1, line_dash="dash", line_color=theme.MUTED)

    theme.apply_theme(fig)
    fig.update_layout(
        margin=dict(l=8, r=16, t=30, b=8),
        height=420,
        hovermode='x unified'
    )
    
    # Metrics
    dir_acc = res['dir_acc'] * 100
    
    warning_chip = None
    if dir_acc < 55:
        warning_chip = html.Div(
            [html.I(className="bi bi-exclamation-triangle"), " Weak signal — model near coin-flip on this stock"],
            className="chip chip-warn",
            style={"marginTop": "16px"}
        )
        
    metrics_row = dbc.Row([
        dbc.Col(StatCard("DIRECTIONAL ACCURACY", f"{dir_acc:.1f}%", 0, 0, "pred-acc"), md=3),
        dbc.Col(StatCard("RMSE (LOG RET)", res['rmse'], 0, 0, "pred-rmse"), md=3),
        dbc.Col(StatCard("MAE (LOG RET)", res['mae'], 0, 0, "pred-mae"), md=3),
        dbc.Col(StatCard("FORECAST PRICE", fc_price, fc_price - last_close, ((fc_price/last_close)-1)*100, "pred-fc"), md=3),
    ])
    
    # Feature Importance (if XGBoost)
    feat_imp_div = html.Div()
    if 'feature_importance' in res:
        fi = res['feature_importance'].head(10)
        fig_fi = px.bar(fi, x='importance', y='feature', orientation='h')
        fig_fi.update_traces(marker_color=theme.ACCENT, marker_line=dict(width=0))
        theme.apply_theme(fig_fi)
        fig_fi.update_layout(
            margin=dict(l=8, r=16, t=8, b=8),
            height=300,
            showlegend=False
        )
        feat_imp_div = html.Div(className="terminal-card", children=[
            html.Div("Feature Importance", className="card-title"),
            dcc.Graph(figure=fig_fi, config={'displayModeBar': False})
        ], style={"marginTop": "24px"})
    
    return html.Div([
        html.Div(className="terminal-card", children=[
            html.Div("Forecast Trajectory", className="card-title"),
            dcc.Graph(figure=fig, config={'displayModeBar': False}),
            warning_chip
        ]),
        metrics_row,
        feat_imp_div
    ])
