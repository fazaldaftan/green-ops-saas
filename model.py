import pandas as pd
import numpy as np
import requests
from prophet import Prophet
from datetime import datetime, timedelta

class NetworkDataConnector:
    """Handles real-time data ingestion from Network OSS/NMS"""
    def __init__(self, tower_id):
        self.tower_id = tower_id
        # In a real app, you'd load these from st.secrets
        self.api_endpoint = "https://nms.telecom-provider.com/api/v1/telemetry"

    def fetch_live_traffic(self, days=30):
        """
        FETCH LOGIC: Replace this with your actual DB query (SQL/InfluxDB)
        For now, we 'replay' a realistic pattern synchronized to the current moment.
        """
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        start_date = now - timedelta(days=days)
        
        # In PROD: response = requests.get(f"{self.api_endpoint}/{self.tower_id}")
        # MOCKING REAL-TIME SYNC:
        dates = pd.date_range(start=start_date, end=now, freq='h')
        
        # Real patterns: Weekend dips + Nightly lows + 2026 5G baseline
        hour = dates.hour
        is_weekend = dates.dayofweek >= 5
        traffic = 60 + 80 * np.sin(2 * np.pi * (hour-6) / 24) # Peak at evening
        traffic[is_weekend] *= 0.8 # Less traffic on weekends in business hubs like Pimpri
        
        # Add 'Live' jitter
        traffic += np.random.normal(0, 5, len(dates))
        
        return pd.DataFrame({'ds': dates, 'y': np.maximum(traffic, 5)})

def get_live_weather(lat, lon):
    """Fetches real-time + 7 day forecast from Open-Meteo"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,precipitation,cloud_cover",
        "timezone": "auto", "past_days": 7
    }
    r = requests.get(url, params=params)
    data = r.json()['hourly']
    
    df = pd.DataFrame({
        'ds': pd.to_datetime(data['time']),
        'temp': data['temperature_2m'],
        'precip': data['precipitation'],
        'cloud': data['cloud_cover']
    })
    return df

def train_and_predict_live(tower_id, lat=18.62, lon=73.80):
    """The production loop: Fetch -> Merge -> Train -> Predict"""
    connector = NetworkDataConnector(tower_id)
    
    # 1. Fetch Real Historical Data (Last 30 days)
    hist_traffic = connector.fetch_live_traffic()
    
    # 2. Fetch Weather (Past + Future)
    weather = get_live_weather(lat, lon)
    
    # 3. Merge for training (Prophet needs 'ds', 'y', and regressors)
    train_df = pd.merge(hist_traffic, weather, on='ds', how='inner')
    
    # 4. Train Model
    model = Prophet(changepoint_prior_scale=0.05, daily_seasonality=True)
    model.add_regressor('precip')
    model.add_regressor('temp')
    model.fit(train_df)
    
    # 5. Predict 48 hours ahead
    future = model.make_future_dataframe(periods=48, freq='h')
    future = pd.merge(future, weather, on='ds', how='left').fillna(0)
    forecast = model.predict(future)
    
    return train_df, forecast
