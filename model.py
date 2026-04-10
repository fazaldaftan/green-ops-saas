import pandas as pd
import numpy as np
import requests
from prophet import Prophet
from datetime import datetime, timedelta

class NetworkDataConnector:
    """Handles real-time data ingestion from Network OSS/NMS"""
    def __init__(self, tower_id):
        self.tower_id = tower_id

    def fetch_live_traffic(self, days=30):
        """FETCH LOGIC: Fixed Index immutability error"""
        # Set 'now' to current time for 'Live' feel
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        start_date = now - timedelta(days=days)
        
        # 1. Generate the date range
        dates = pd.date_range(start=start_date, end=now, freq='h')
        
        # --- THE FIX ---
        # Convert Index to Numpy values so the resulting 'traffic' array is mutable
        hour = dates.hour.values
        dayofweek = dates.dayofweek.values
        is_weekend = dayofweek >= 5
        
        # 2. Calculate traffic as a mutable numpy array
        # Pattern: Peak at 8 PM (20:00), low at 4 AM
        traffic = 70 + 90 * np.sin(2 * np.pi * (hour - 14) / 24) 
        
        # Apply weekend discount (Mutable operation now allowed)
        traffic[is_weekend] *= 0.75 
        
        # Add realistic noise
        np.random.seed(42)
        traffic += np.random.normal(0, 8, len(dates))
        traffic = np.maximum(traffic, 10) # Floor at 10 Mbps
        
        return pd.DataFrame({'ds': dates, 'y': traffic})

def get_live_weather(lat, lon):
    """Fetches real-time + 7 day forecast from Open-Meteo"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,precipitation,cloud_cover",
        "timezone": "Asia/Kolkata", "past_days": 7, "forecast_days": 3
    }
    r = requests.get(url, params=params, timeout=15)
    data = r.json()['hourly']
    
    df = pd.DataFrame({
        'ds': pd.to_datetime(data['time']),
        'temp': data['temperature_2m'],
        'precip': data['precipitation'],
        'cloud': data['cloud_cover']
    })
    # Remove timezone for Prophet compatibility
    df['ds'] = df['ds'].dt.tz_localize(None)
    return df

def train_and_predict_live(tower_id):
    """Full Pipeline: Fetch -> Train -> Predict"""
    # Location for Pimpri-Chinchwad
    lat, lon = 18.62, 73.80
    
    connector = NetworkDataConnector(tower_id)
    hist_traffic = connector.fetch_live_traffic(days=14) # Use 14 days for faster demo
    weather = get_live_weather(lat, lon)
    
    # Merge historical data with weather
    train_df = pd.merge(hist_traffic, weather, on='ds', how='inner')
    
    # Model configuration for 2026 high-frequency data
    model = Prophet(
        changepoint_prior_scale=0.05, 
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False
    )
    model.add_regressor('precip')
    model.add_regressor('temp')
    model.fit(train_df)
    
    # Forecast 48 hours into the future
    future = model.make_future_dataframe(periods=48, freq='h')
    future = pd.merge(future, weather, on='ds', how='left').fillna(0)
    forecast = model.predict(future)
    
    # Product Logic: Recommendations
    forecast['hour'] = forecast['ds'].dt.hour
    def get_rec(row):
        if row['precip'] > 2.0: return "🔴 FULL POWER (Weather Alert)"
        if row['yhat'] < 40 and 1 <= row['hour'] <= 5: return "🟢 THROTTLE 40% (Deep Sleep)"
        if row['yhat'] < 70: return "🟡 THROTTLE 20% (Optimized)"
        return "🔴 FULL POWER"
        
    forecast['recommendation'] = forecast.apply(get_rec, axis=1)
    
    return train_df, forecast
