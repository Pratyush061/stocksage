import pytest
import pandas as pd
import numpy as np
from analytics.models import XGBoostWalkForward

def test_xgboost_trains():
    dates = pd.date_range('2023-01-01', periods=100, freq='B')
    df = pd.DataFrame({
        'Open': np.random.randn(100) + 100,
        'High': np.random.randn(100) + 105,
        'Low': np.random.randn(100) + 95,
        'Close': np.random.randn(100) + 100,
        'Volume': np.random.randint(1000, 10000, size=100)
    }, index=dates)
    
    model = XGBoostWalkForward(horizon=1)
    res = model.train_and_predict(df)
    
    assert 'rmse' in res
    assert 'mae' in res
    assert 'forecast' in res
    assert isinstance(res['forecast'], (float, np.floating))
    assert 'full_preds' in res
    assert isinstance(res['full_preds'], pd.Series)
