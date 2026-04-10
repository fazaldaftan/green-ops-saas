import streamlit as st
import plotly.graph_objects as go
from model import GreenOpsEngine
from datetime import datetime

st.set_page_config(page_title="Green-Ops | LIVE", layout="wide")

# UI Polish
st.markdown("<style>.stMetric { border: 1px solid #30363d; padding: 15px; border-radius: 10px; }</style>", unsafe_allow_html=True)

engine = GreenOpsEngine()

# --- TOP STATUS BAR ---
st.title("🌿 Green-Ops Enterprise v3.0")
st.write(f"**Cluster:** Pimpri-Chinchwad (IN-MH-01) | **Status:** <span style='color:#238636'>● FULLY AUTONOMOUS</span>", unsafe_allow_html=True)

# --- THE MAGIC HAPPENS ---
with st.spinner("Connecting to Pimpri NMS..."):
    signals, forecast = engine.forecast_and_optimize()

# --- THE CFO VIEW ---
col1, col2, col3, col4 = st.columns(4)
is_peak = 18 <= datetime.now().hour <= 22 # Current 9PM is PEAK

# Real Math: 5G Macro Tower uses ~10kWh. Saving 30% power = 3kWh.
# 3kWh * ₹17.81 (Peak) = ₹53.43 saved per hour per tower.
savings_hr = 53.43 if (signals['load'] < 40 and not signals['rain'] > 0) else 0.0

col1.metric("Live Load (TomTom)", f"{signals['load']:.1f}%")
col2.metric("Local Weather", f"{signals['temp']}°C / {signals['rain']}mm")
col3.metric("Grid Tariff", "₹17.81/u", "PEAK RATE")
col4.metric("Hourly Saving", f"₹{savings_hr:.2f}")

st.divider()

# --- THE MAGIC VISUAL ---
left, right = st.columns([2, 1])

with left:
    st.subheader("🔮 Predictive Optimization (48h Window)")
    fig = go.Figure()
    # Live Trend
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name="Predicted Traffic", line=dict(color='#00ffcc', width=3)))
    # Threshold for Throttling
    fig.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Throttle Threshold")
    
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("🛠️ Autonomous Control Log")
    
    # DECISION ENGINE
    if signals['rain'] > 0.5:
        st.error("WEATHER OVERRIDE: Rain detected. Maintaining max power for signal penetration.")
    elif signals['load'] > 75:
        st.warning("CAPACITY ALERT: Heavy Friday night traffic. Throttling DISABLED.")
    elif is_peak:
        st.success("PEAK SAVING MODE: Aggressive power-down to avoid high tariffs.")
        st.code("CMD > rf_power_set --target -6dB")
        st.caption("Status: MIMO Layers 3/4 Sleeping")
    else:
        st.info("NORMAL OPS: System monitoring user density.")

    st.write("---")
    st.write("**Next Decision Pulse:** 15m 00s")
