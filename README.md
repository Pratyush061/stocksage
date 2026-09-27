# StockSage India — NSE Market Intelligence & ML Prediction Dashboard

StockSage India is a stock market prediction and analysis platform for the Indian markets (NSE/BSE). It provides live-quality market data, professional technical analysis charts, ML-driven price forecasts with honest confidence bands, a quant-style screener, and strategy backtesting with modern risk metrics.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

## Architecture

- **Data Layer:** Fetches market data using `yfinance` with 15-min intraday caching and 24h daily caching via `Flask-Caching`.
- **Analytics Layer:** Computes technical indicators, engineered features, walk-forward XGBoost and LSTM models.
- **Presentation Layer:** Multi-page Dash application using `dash-bootstrap-components` with a custom dark "trading terminal" aesthetic.

## Paid Data Feed Migration

Currently, the application uses `yfinance`. To swap in a paid data feed (e.g., Zerodha Kite or Alpha Vantage):
1. Update `data/market_data.py`.
2. Replace `yf.Ticker(symbol).history(...)` with the new API call.
3. Ensure the returned format matches a Pandas DataFrame with standard OHLCV columns (`Open`, `High`, `Low`, `Close`, `Volume`).

## Model Retraining & Limitations

Models are cached in `models/cache/`. To retrain, simply clear this directory.
**Limitations:** Machine learning on financial markets is subject to the efficient-market hypothesis. Models are heavily prone to overfitting, which is why we enforce strict walk-forward validation and no look-ahead features. The predictions are for educational purposes only.
