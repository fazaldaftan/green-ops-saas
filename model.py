import pandas as pd
import numpy as np
import streamlit as st
import requests
from prophet import Prophet
from datetime import datetime

def generate_traffic_data():
    """Generate synthetic traffic data for Pimpri-like pattern"""
    dates = pd.date_range(start='2026-03-01', periods=720, freq='H')
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
    if times.tz is None:
        times = times.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        times = times.tz_convert('Asia/Kolkata')
    
    weather_df = pd.DataFrame({
        'ds': times.tz_localize(None),
        'temperature_2m': hourly['temperature_2m'],
        'precipitation': hourly['precipitation'],
        'wind_speed_10m': hourly['wind_speed_10m'],
        'cloud_cover': hourly['cloud_cover']
    })
    weather_df['ds'] = weather_df['ds'].dt.floor('H')
    return weather_df

def train_and_predict():
    """Train model and return forecast with recommendations"""
    df = generate_traffic_data()
    weather_df = get_pune_weather()
    
    # Merge
    df_merged = pd.merge(df, weather_df[['ds', 'precipitation', 'cloud_cover', 'temperature_2m']], 
                         on='ds', how='left').fillna(0)
    
    # Train Prophet
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False,
        interval_width=0.8
    )
    model.add_regressor('precipitation')
    model.add_regressor('cloud_cover')
    model.add_regressor('temperature_2m')
    model.fit(df_merged[['ds', 'y', 'precipitation', 'cloud_cover', 'temperature_2m']])
    
    # Predict next 48 hours
    future = model.make_future_dataframe(periods=48, freq='H')
    future = pd.merge(future, weather_df[['ds', 'precipitation', 'cloud_cover', 'temperature_2m']], 
                      on='ds', how='left').fillna(0)
    forecast = model.predict(future)
    
    # Recommendation logic
    def recommend_power_mode(pred_traffic, hour, precip):
        if precip > 3.0:
            return "🔴 FULL POWER - Rain may increase traffic"
        if pred_traffic < 45 and 1 <= hour <= 5:
            return "🟢 THROTTLE 40% - Safe to sleep carriers"
        elif pred_traffic < 75:
            return "🟡 THROTTLE 20-30% - Good saving opportunity"
        else:
            return "🔴 FULL POWER - Normal operation"
    
    forecast['hour'] = forecast['ds'].dt.hour
    forecast['recommendation'] = forecast.apply(
        lambda row: recommend_power_mode(row['yhat'], row['hour'], row.get('precipitation', 0)), 
        axis=1
    )
    
    return df, forecast, weather_df

def get_savings_estimate(forecast):
    """Simple savings calculator"""
    throttle_count = forecast['recommendation'].str.contains('THROTTLE').sum()
    total_hours = len(forecast)
    savings_percent = round((throttle_count / total_hours) * 35, 1)  # assume avg 35% saving when throttling
    return savings_percent
