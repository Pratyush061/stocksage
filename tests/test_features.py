import pytest
import pandas as pd
import numpy as np
from analytics.features import engineer_features

def test_no_lookahead_bias():
    dates = pd.date_range('2023-01-01', periods=50, freq='B')
    df = pd.DataFrame({
        'Open': np.random.randn(50) + 100,
        'High': np.random.randn(50) + 105,
        'Low': np.random.randn(50) + 95,
        'Close': np.random.randn(50) + 100,
        'Volume': np.random.randint(1000, 10000, size=50)
    }, index=dates)
    
    # Calculate features on full df
    feat_full = engineer_features(df)
    
    # Calculate features on df up to T-1
    t = 40
    df_partial = df.iloc[:t].copy()
    feat_partial = engineer_features(df_partial)
    
    # Check that features at index T-2 are identical (T-1 target will differ since it needs T)
    # The requirement is that features at time t use only data <= t.
    
    features = [c for c in feat_full.columns if c not in ['target']]
    
    for c in features:
        val_full = feat_full[c].iloc[t-2]
        val_partial = feat_partial[c].iloc[t-2]
        if pd.isna(val_full):
            assert pd.isna(val_partial)
        else:
            assert np.isclose(val_full, val_partial), f"Feature {c} leaked future data!"
