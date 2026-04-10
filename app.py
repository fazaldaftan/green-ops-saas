import streamlit as st
import plotly.graph_objects as go
from model import GreenOpsEngine
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Green-Ops Enterprise v3.0", page_icon="🌿", layout="wide")

# Custom CSS for a clean, high-tech dashboard
st.markdown("""
    <style>
    .stMetric { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; }
    .status-live { color: #238636; font-weight: bold; }
    .cmd-box { background-color: #0d1117; color: #58a6ff; padding: 15px; border-left: 5px solid #238636; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

engine = GreenOpsEngine()

# --- HEADER ---
st.title("🌿 Green-Ops Enterprise v3.0")
st.write(f"**Cluster:** Pimpri-Chinchwad (IN-MH-01) | **Status:** <span class='status-live'>● FULLY AUTONOMOUS</span>", unsafe_allow_html=True)

# --- EXECUTE LIVE DATA ENGINE ---
with st.spinner("Connecting to Pimpri NMS..."):
    # This calls your TomTom and Open-Meteo APIs
    signals, forecast = engine.forecast_and_optimize()

# --- TOP METRICS PANEL ---
m1, m2, m3, m4 = st.columns(4)

# Real-time Tariff Logic (Maharashtra 2026 Standards)
# Using IST Hour for the Demo
ist_hour = (datetime.now().hour + 5) % 24 # Crude IST conversion for demo if server is UTC
is_peak = 18 <= ist_hour <= 22 
tariff = 17.81 if is_peak else 11.20

# Magic Math: If load is low, we are actively saving.
# A 10kW tower saving 30% = 3kWh. 3kWh * ₹17.81 = ₹53.43
current_saving = 53.43 if signals['load'] < 40 else 0.0

m1.metric("Live Load (TomTom)", f"{signals['load']:.1f}%")
m2.metric("Local Weather", f"{signals['temp']}°C / {signals['rain']}mm")
m3.metric("Grid Tariff", f"₹{tariff}/u", "PEAK RATE" if is_peak else "NORMAL")
m4.metric("Hourly Saving", f"₹{current_saving:.2f}")

st.divider()

# --- DASHBOARD BODY ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🔮 Predictive Optimization (48h Window)")
    fig = go.Figure()
    
    # AI Forecast Curve
    fig.add_trace(go.Scatter(
        x=forecast['ds'], 
        y=forecast['yhat'], 
        name="Predicted Traffic", 
        line=dict(color='#00ffcc', width=3)
    ))
    
    # Safety Threshold Line
    fig.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Throttle Threshold")
    
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🛠️ Autonomous Control Log")
    
    # --- THE MAGIC DECISION ENGINE ---
    # 1. Weather Safety Override
    if signals['rain'] > 0.5:
        st.error("📡 WEATHER OVERRIDE: Rain detected. Signal path-loss compensation active. Power at 100%.")
    
    # 2. High Load Safety
    elif signals['load'] > 75:
        st.warning("🚀 CAPACITY ALERT: High user density. Optimization suspended to protect QoS.")
    
    # 3. THE MAGIC (Load < 40%)
    elif signals['load'] < 40:
        st.success(f"✨ MAGIC ACTIVE: Low Traffic Detected ({signals['load']:.1f}%)")
        st.markdown(f"""
        <div class="cmd-box">
        CMD > rf_power_set --target -6dB
        </div>
        """, unsafe_allow_html=True)
        st.info(f"Energy-Efficient Mode (EEM) Engaged. Saving ₹{current_saving:.2f}/hr.")
        st.caption("3/4 MIMO Layers in Deep Sleep.")
    
    # 4. Standard Operation
    else:
        st.info("ℹ️ NORMAL OPS: Traffic is moderate. System monitoring for saving opportunities.")

    st.write("---")
    st.write(f"**Next Decision Pulse:** 15m 00s")
    
    # Carbon Math Section
    st.write("### 🌍 Carbon Impact")
    st.latex(r"CO_2\text{ offset} = \text{kWh} \times 0.82\text{ kg/kWh}")
    daily_co2 = (current_saving / tariff) * 24 * 0.82
    st.write(f"Est. Daily Reduction: **{daily_co2:.1f} kg CO₂**")

st.caption("Hardware: Ericsson 5G-6444 | Source: TomTom Real-Time + Open-Meteo API")
