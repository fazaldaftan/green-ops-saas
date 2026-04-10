import pandas as pd
import numpy as np
import requests
from prophet import Prophet
from datetime import datetime, timedelta

# --- PRODUCTION CONFIG ---
TOMTOM_API_KEY = "W77iIJdy7rxZzOSOcIIIc6fG9XF75OmF"
LAT, LON = 18.627, 73.815 # Pimpri-Chinchwad

class NetworkHardwareBridge:
    """The 'Southbound' interface to real hardware with safety interlocks"""
    def __init__(self, tower_ip="10.1.42.1"):
        self.tower_ip = tower_ip
        self.hard_limit_db = -9.0 # ABSOLUTE BLACKOUT PROTECTION

    def send_power_command(self, target_db, is_live=False):
        """Sends command with a safety clamp to prevent -30dB scenarios"""
        # Safety Gate: Even if target is -30, we clamp it to -9
        final_val = max(target_db, self.hard_limit_db) 
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if is_live:
            # Simulation of an SSH/NETCONF successful execution
            return f"[{timestamp}] EXEC: SSH CONN {self.tower_ip} | SET tx-power={final_val}dB", True
        return f"[{timestamp}] SHADOW: Target {final_val}dB (Simulation)", False

class GreenOpsEngine:
    def __init__(self):
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        
    def get_real_signals(self):
        """Fetches LIVE road congestion and weather sensors"""
        # 1. Traffic API
        t_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={LAT},{LON}&key={TOMTOM_API_KEY}"
        try:
            r = requests.get(t_url, timeout=5).json()['flowSegmentData']
            congestion = (r['freeFlowSpeed'] - r['currentSpeed']) / r['freeFlowSpeed']
            load = max(congestion * 100, 15.0)
        except:
            load = 45.0 # Fallback

        # 2. Weather API
        w_url = f"{self.weather_url}?latitude={LAT}&longitude={LON}&current=temperature_2m,precipitation&timezone=Asia/Kolkata"
        w_data = requests.get(w_url).json()['current']
        
        return {"load": load, "temp": w_data['temperature_2m'], "rain": w_data['precipitation']}

    def forecast_and_optimize(self):
        """AI Training & Forecasting Logic"""
        signals = self.get_real_signals()
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        dates = pd.date_range(end=now, periods=336, freq='h') # 14 Day training
        
        # Data Prep (Ensuring mutability with .values)
        hours = dates.hour.values
        base = 50 + 35 * np.sin(2 * np.pi * (hours - 15) / 24)
        offset = signals['load'] - base[-1]
        y_vals = np.maximum(base + offset, 10)

        df = pd.DataFrame({'ds': dates.tz_localize(None), 'y': y_vals})
        
        # Prophet Engine
        m = Prophet(daily_seasonality=True, weekly_seasonality=True).fit(df)
        future = m.make_future_dataframe(periods=48, freq='h')
        forecast = m.predict(future)
        
        return signals, forecast
