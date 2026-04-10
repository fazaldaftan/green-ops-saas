import streamlit as st
import plotly.graph_objects as go
from model import train_and_predict, get_savings_estimate

st.set_page_config(page_title="Green-Ops SaaS", layout="wide")
st.title("🌿 AI-Driven Green-Ops for Cell Towers")
st.markdown("**Weather-Aware Traffic Prediction & Power Saving** — Pimpri, Maharashtra Demo")

# Run the model
with st.spinner("Training model with live weather..."):
    historical_df, forecast, weather_df = train_and_predict()

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Traffic Forecast (Next 48 Hours)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=historical_df['ds'], y=historical_df['y'], 
                             name='Historical Traffic', mode='lines'))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], 
                             name='Predicted Traffic', mode='lines'))
    fig.update_layout(height=500, title="Cell Tower Traffic + Prediction")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("⚡ Green-Ops Recommendations")
    st.dataframe(
        forecast[['ds', 'yhat', 'precipitation', 'recommendation']].tail(24),
        use_container_width=True,
        hide_index=True
    )
    
    savings = get_savings_estimate(forecast)
    st.metric(label="Estimated Power Savings", value=f"{savings}%", 
              delta="in low-traffic periods")

st.info("💰 In real deployment this could save **₹2–5 Lakh per tower per year** depending on electricity rates.")

st.caption("Green-Ops SaaS MVP | Built with Prophet + Open-Meteo | Deployed via Streamlit Cloud")