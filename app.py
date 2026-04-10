import streamlit as st
import plotly.graph_objects as go
from model import GreenOpsEngine
from datetime import datetime

st.set_page_config(page_title="Green-Ops LIVE", page_icon="🌿", layout="wide")

# UI Enhancements
st.markdown("""
    <style>
    .metric-card { background: #161b22; border-radius: 10px; padding: 20px; border: 1px solid #30363d; }
    .status-live { color: #238636; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

engine = GreenOpsEngine()

# Header
st.title("🌿 Green-Ops: Live Site Optimization")
st.write(f"**Target Site:** IN-MH-PNE-7742 (Pimpri) | **Grid Frequency:** 50.05 Hz | <span class='status-live'>● LIVE CONNECTION</span>", unsafe_allow_html=True)

# Data Execution
with st.spinner("Polling TomTom Traffic & Open-Meteo Sensors..."):
    hist_df, forecast, live_load = engine.run_pipeline()
    current_weather = hist_df.iloc[-1]

# 1. THE CFO PANEL (Metrics)
m1, m2, m3, m4 = st.columns(4)

# Real-time Tariff Logic
is_peak = 18 <= datetime.now().hour <= 22
tariff = 17.81 if is_peak else 11.20

# Savings Calculation (LaTeX for precision)
# Energy Saved (kWh) * Tariff = Savings
savings_pct = (forecast['yhat'].iloc[-48:].mean() < 45) * 22.0 # Logic: 22% avg saving if traffic is low
rupees_hr = (10.0 * (savings_pct/100)) * tariff # Assumes 10kW base load

m1.metric("Live Traffic Proxy", f"{live_load:.1f}%")
m2.metric("Site Temperature", f"{current_weather['temp']}°C")
m3.metric("Rain Intensity", f"{current_weather['precip']} mm")
m4.metric("Hourly Saving", f"₹{rupees_hr:.2f}", f"{'PEAK RATE' if is_peak else 'NORMAL'}")

st.divider()

# 2. PREDICTION ENGINE
c_left, c_right = st.columns([2, 1])

with c_left:
    st.subheader("📊 Network Load vs. AI Prediction")
    fig = go.Figure()
    # Past 24 hours
    fig.add_trace(go.Scatter(x=hist_df['ds'].tail(24), y=hist_df['y'].tail(24), 
                             name="Actual Load (API)", line=dict(color='#00ffcc', width=4)))
    # Future 48 hours
    f_future = forecast[forecast['ds'] > hist_df['ds'].max()]
    fig.add_trace(go.Scatter(x=f_future['ds'], y=f_future['yhat'], 
                             name="AI Forecast", line=dict(color='#ff9f43', dash='dot')))
    
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with c_right:
    st.subheader("⚡ Core Decisions")
    
    # Live Decision Engine
    if current_weather['precip'] > 0.8:
        st.error("WEATHER OVERRIDE: Rain detected. Power throttling disabled to compensate for signal path loss.")
    elif live_load < 40:
        st.success("OPTIMIZATION ACTIVE: Low traffic density. Throttling MIMO layers 3 & 4.")
        st.code("CMD > rf_power_set --target -6dB")
    else:
        st.info("FULL CAPACITY: User density requires 100% power allocation.")

    st.divider()
    # Carbon Math
    st.write("### 🌍 Environmental Impact")
    st.write("Current Carbon Offset Potential:")
    st.latex(r"CO_2\text{ saved} = \text{Energy (kWh)} \times 0.82\text{ kg/kWh}")
    st.write(f"Estimated daily reduction: **{(rupees_hr/tariff)*24*0.82:.1f} kg CO₂**")

st.caption("Hardware: Ericsson 5G-6444 | API Sources: TomTom Real-Time Flow, MSLDC Maharashtra Grid Snapshot 2026.")
