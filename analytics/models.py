import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os
import pickle
import hashlib
from analytics.features import engineer_features

# Cache directory for models
CACHE_DIR = 'models/cache/'
os.makedirs(CACHE_DIR, exist_ok=True)

class XGBoostWalkForward:
    def __init__(self, horizon: int = 1, retrain_step: int = 21):
        self.horizon = horizon
        self.retrain_step = retrain_step
        self.models_q01 = []
        self.models_q50 = []
        self.models_q90 = []
        
    def _prepare_data(self, df: pd.DataFrame):
        df_feat = engineer_features(df).dropna()
        
        # Adjust target for horizon if needed (e.g. 5 days ahead)
        if self.horizon > 1:
            df_feat['target'] = np.log(df_feat['Close'].shift(-self.horizon) / df_feat['Close'])
            df_feat = df_feat.dropna()
            
        features = [c for c in df_feat.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'target', 'day_of_week', 'month']]
        X = df_feat[features]
        y = df_feat['target']
        return X, y, features
        
    def train_and_predict(self, df: pd.DataFrame):
        X, y, features = self._prepare_data(df)
        
        # Simple train-test split for walk-forward approximation in this demo
        # A true walk-forward would iterate over windows. We'll do an 80/20 split
        # and just train once for the scope of this dashboard responsiveness.
        split_idx = int(len(X) * 0.8)
        
        X_train, y_train = X.iloc[:split_idx], y.iloc[:split_idx]
        X_test, y_test = X.iloc[split_idx:], y.iloc[split_idx:]
        
        # Parameters for quantile regression
        params_base = {
            'max_depth': 5,
            'n_estimators': 100, # reduced for speed, normally 800
            'learning_rate': 0.1,
            'objective': 'reg:squarederror'
        }
        
        # Med model
        model_median = xgb.XGBRegressor(**params_base)
        model_median.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        
        # Predict on test
        preds = model_median.predict(X_test)
        
        # Calculate metrics
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mae = mean_absolute_error(y_test, preds)
        
        # Directional accuracy
        # Both actual and predicted return direction
        actual_dir = np.sign(y_test)
        pred_dir = np.sign(preds)
        dir_acc = np.mean(actual_dir == pred_dir)
        
        # Feature importance
        importance = model_median.feature_importances_
        feature_importance = pd.DataFrame({'feature': features, 'importance': importance}).sort_values(by='importance', ascending=False)
        
        # Forecast out of sample (next horizon)
        last_row = X.iloc[-1:]
        next_pred = model_median.predict(last_row)[0]
        
        # Simple residuals for bands (since true quantile xgb requires custom objective in some xgb versions)
        residuals = y_test - preds
        std_res = np.std(residuals)
        lower_band = next_pred - 1.28 * std_res # roughly 80% CI
        upper_band = next_pred + 1.28 * std_res
        
        # Return full prediction series for plotting
        full_preds = model_median.predict(X)
        full_pred_series = pd.Series(full_preds, index=X.index)
        
        return {
            'rmse': rmse,
            'mae': mae,
            'dir_acc': dir_acc,
            'forecast': next_pred,
            'forecast_lower': lower_band,
            'forecast_upper': upper_band,
            'feature_importance': feature_importance,
            'full_preds': full_pred_series,
            'train_end_date': X_train.index[-1]
        }

class LSTMModel:
    def __init__(self, horizon: int = 1):
        self.horizon = horizon
        
    def _prepare_data(self, df: pd.DataFrame):
        df_feat = engineer_features(df).dropna()
        if self.horizon > 1:
            df_feat['target'] = np.log(df_feat['Close'].shift(-self.horizon) / df_feat['Close'])
            df_feat = df_feat.dropna()
            
        features = [c for c in df_feat.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'target', 'day_of_week', 'month']]
        X = df_feat[features].values
        y = df_feat['target'].values
        return X, y, df_feat.index, features
        
    def train_and_predict(self, df: pd.DataFrame):
        import tensorflow as tf
        from keras.models import Sequential
        from keras.layers import LSTM, Dense, Dropout
        from sklearn.preprocessing import StandardScaler
        
        X, y, index, features = self._prepare_data(df)
        
        # Scale
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Sequence generation (60 days)
        seq_len = 60
        X_seq, y_seq = [], []
        if len(X_scaled) <= seq_len:
            return None # Not enough data
            
        for i in range(seq_len, len(X_scaled)):
            X_seq.append(X_scaled[i-seq_len:i])
            y_seq.append(y[i])
            
        X_seq, y_seq = np.array(X_seq), np.array(y_seq)
        
        split = int(len(X_seq) * 0.9)
        X_train, y_train = X_seq[:split], y_seq[:split]
        X_val, y_val = X_seq[split:], y_seq[split:]
        
        # Model
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(seq_len, X_train.shape[2])),
            Dropout(0.2),
            LSTM(64),
            Dropout(0.2),
            Dense(1)
        ])
        
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3), loss='mse')
        
        # Train (minimal epochs for demo speed)
        model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=5, batch_size=32, verbose=0)
        
        # Predict
        val_preds = model.predict(X_val).flatten()
        rmse = np.sqrt(mean_squared_error(y_val, val_preds))
        mae = mean_absolute_error(y_val, val_preds)
        
        actual_dir = np.sign(y_val)
        pred_dir = np.sign(val_preds)
        dir_acc = np.mean(actual_dir == pred_dir)
        
        # Next forecast
        last_seq = X_scaled[-seq_len:].reshape(1, seq_len, X_scaled.shape[1])
        next_pred = model.predict(last_seq)[0][0]
        
        std_res = np.std(y_val - val_preds)
        lower = next_pred - 1.28 * std_res
        upper = next_pred + 1.28 * std_res
        
        full_preds = model.predict(X_seq).flatten()
        pred_index = index[seq_len:]
        full_pred_series = pd.Series(full_preds, index=pred_index)
        
        return {
            'rmse': rmse,
            'mae': mae,
            'dir_acc': dir_acc,
            'forecast': next_pred,
            'forecast_lower': lower,
            'forecast_upper': upper,
            'full_preds': full_pred_series
        }

def get_predictions(df: pd.DataFrame, model_type: str, horizon: int):
    """Entry point for Dash to get predictions with caching."""
    # Hash data to use as cache key
    data_hash = hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()
    cache_file = os.path.join(CACHE_DIR, f"{model_type}_{horizon}_{data_hash}.pkl")
    
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
            
    if model_type == 'XGBoost':
        model = XGBoostWalkForward(horizon=horizon)
        res = model.train_and_predict(df)
    elif model_type == 'LSTM':
        model = LSTMModel(horizon=horizon)
        res = model.train_and_predict(df)
    else:
        # Ensemble (average)
        xgb_mod = XGBoostWalkForward(horizon=horizon)
        lstm_mod = LSTMModel(horizon=horizon)
        r1 = xgb_mod.train_and_predict(df)
        r2 = lstm_mod.train_and_predict(df)
        
        if r2 is None:
            res = r1 # fallback
        else:
            # simple average for demo
            fc = (r1['forecast'] + r2['forecast']) / 2
            lb = (r1['forecast_lower'] + r2['forecast_lower']) / 2
            ub = (r1['forecast_upper'] + r2['forecast_upper']) / 2
            
            common_idx = r1['full_preds'].index.intersection(r2['full_preds'].index)
            fp = (r1['full_preds'][common_idx] + r2['full_preds'][common_idx]) / 2
            
            res = {
                'rmse': (r1['rmse'] + r2['rmse'])/2,
                'mae': (r1['mae'] + r2['mae'])/2,
                'dir_acc': (r1['dir_acc'] + r2['dir_acc'])/2,
                'forecast': fc,
                'forecast_lower': lb,
                'forecast_upper': ub,
                'full_preds': fp,
                'feature_importance': r1['feature_importance']
            }
            
    with open(cache_file, 'wb') as f:
        pickle.dump(res, f)
        
    return res
