import pandas as pd
import numpy as np
import requests
from prophet import Prophet
from datetime import datetime

def generate_traffic_data():
    """Generate synthetic traffic data for Pimpri-like pattern"""
    # FIX: Changed 'H' to 'h' for Pandas 3.0+ compatibility
    dates = pd.date_range(start='2026-03-01', periods=720, freq='h')
    np.random.seed(42)
    hour = dates.hour
    dayofweek = dates.dayofweek

    base_traffic = 50 + 100 * np.sin(2 * np.pi * hour / 24) + 30 * (dayofweek < 5)
    base_traffic += np.random.normal(0, 15, len(dates))

    df = pd.DataFrame({
        'ds': dates,
        'y': np.maximum(base_traffic, 10),
        'hour': hour,
        'dayofweek': dayofweek
    })
    return df

def get_pune_weather():
    """Fetch live weather for Pimpri (18.62, 73.80)"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 18.62,
        "longitude": 73.80,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,cloud_cover",
        "timezone": "Asia/Kolkata",
        "forecast_days": 7
    }
    
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    hourly = data['hourly']
    
    times = pd.to_datetime(hourly['time'])
    # Ensure times are naive for Prophet
    if times.tz is not None:
        times = times.tz_convert('Asia/Kolkata').tz_localize(None)
    
    weather_df = pd.DataFrame({
        'ds': times,
        'temperature_2m': hourly['temperature_2m'],
        'precipitation': hourly['precipitation'],
        'wind_speed_10m': hourly['wind_speed_10m'],
        'cloud_cover': hourly['cloud_cover']
    })
    # FIX: Use lowercase 'h' for floor
    weather_df['ds'] = weather_df['ds'].dt.floor('h')
    return weather_df

def train_and_predict():
    """Train model and return forecast with recommendations"""
    df = generate_traffic_data()
    weather_df = get_pune_weather()
    
    # Merge on 'ds'
    df_merged = pd.merge(df, weather_df[['ds', 'precipitation', 'cloud_cover', 'temperature_2m']], 
                         on='ds', how='left').fillna(0)
    
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False
    )
    model.add_regressor('precipitation')
    model.add_regressor('cloud_cover')
    model.add_regressor('temperature_2m')
    
    model.fit(df_merged)
    
    # FIX: Changed 'H' to 'h'
    future = model.make_future_dataframe(periods=48, freq='h')
    future = pd.merge(future, weather_df[['ds', 'precipitation', 'cloud_cover', 'temperature_2m']], 
                      on='ds', how='left').fillna(0)
    
    forecast = model.predict(future)
    
    # Logic for recommendations
    forecast['hour'] = forecast['ds'].dt.hour
    forecast['recommendation'] = forecast.apply(
        lambda row: "🟢 THROTTLE 40%" if row['yhat'] < 45 and 1 <= row['hour'] <= 5 
        else "🔴 FULL POWER", axis=1
    )
    
    return df, forecast, weather_df

def get_savings_estimate(forecast):
    throttle_count = forecast['recommendation'].str.contains('THROTTLE').sum()
    return round((throttle_count / len(forecast)) * 35, 1)
