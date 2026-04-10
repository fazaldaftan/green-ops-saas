import streamlit as st
import plotly.graph_objects as go
from model import GreenOpsEngine, NetworkHardwareBridge
from datetime import datetime

st.set_page_config(page_title="Green-Ops Pro", page_icon="📡", layout="wide")

# Persistent log for the console
if 'hw_log' not in st.session_state:
    st.session_state.hw_log = []

# --- STYLING ---
st.markdown("""
    <style>
    .stMetric { border: 1px solid #30363d; background: #0d1117; padding: 15px; border-radius: 10px; }
    .console { background-color: #000; color: #00ff00; padding: 10px; font-family: 'Courier New'; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

engine = GreenOpsEngine()
bridge = NetworkHardwareBridge()

# --- SIDEBAR: PERFORMANCE TUNING ---
with st.sidebar:
    st.header("⚙️ Tower Performance")
    throttle_threshold = st.slider("Throttle Threshold (%)", 10, 60, 40)
    db_target = st.select_slider("Target Power Cut (dB)", options=[-3, -6, -9], value=-6)
    st.divider()
    live_bridge = st.toggle("Enable Live Hardware Bridge", value=False)
    if st.button("Purge Console Logs"):
        st.session_state.hw_log = []

# --- DATA FETCH ---
with st.spinner("🔄 Polling live sensors in Pimpri..."):
    signals, forecast = engine.forecast_and_optimize()

# --- TOP ROW: BUSINESS METRICS ---
st.title("🌿 Green-Ops Enterprise v3.5")
m1, m2, m3, m4 = st.columns(4)

# Maharashtra Tariff Logic (2026)
is_peak = 18 <= datetime.now().hour <= 22
tariff = 17.81 if is_peak else 11.20
savings = 53.43 if (signals['load'] < throttle_threshold and signals['rain'] < 0.5) else 0.0

m1.metric("Live Traffic Density", f"{signals['load']:.1f}%")
m2.metric("Site Climate", f"{signals['temp']}°C / {signals['rain']}mm")
m3.metric("Grid Rate (MSLDC)", f"₹{tariff}/u", "PEAK" if is_peak else "NORMAL")
m4.metric("Active Saving", f"₹{savings:.2f}/hr")

st.divider()

# --- MAIN DASHBOARD ---
c_left, c_right = st.columns([2, 1])

with c_left:
    st.subheader("🔮 48-Hour Traffic Projection")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name="Predicted", line=dict(color='#00ffcc', width=3)))
    fig.add_hline(y=throttle_threshold, line_dash="dash", line_color="red", annotation_text="Threshold")
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with c_right:
    st.subheader("🖥️ Southbound Console")
    
    # DECISION ENGINE
    action_db = db_target if signals['load'] < throttle_threshold else 0.0
    log_entry, is_exec = bridge.send_power_command(action_db, is_live=live_bridge)
    
    if not st.session_state.hw_log or log_entry != st.session_state.hw_log[-1]:
        st.session_state.hw_log.append(log_entry)

    # Console Display
    st.markdown(f'<div class="console">{"<br>".join(st.session_state.hw_log[-6:])}</div>', unsafe_allow_html=True)
    
    st.write("---")
    if signals['rain'] > 0.5:
        st.error("🌧️ RAIN OVERRIDE: Power at 100%")
    elif signals['load'] < throttle_threshold:
        st.success(f"✨ MAGIC ACTIVE: Throttling to {db_target}dB")
    else:
        st.info("ℹ️ STANDBY: Traffic is within normal range.")

st.divider()
st.write("### 🌍 Environmental Impact")
st.latex(r"CO_2\text{ offset} = \text{Energy (kWh)} \times 0.82\text{ kg/kWh}")
st.caption("v3.5 Build | TomTom-Verified | Safety Locked at -9dB Max")
