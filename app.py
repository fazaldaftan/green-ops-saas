import streamlit as st
import plotly.graph_objects as go
from model import train_and_predict, get_savings_estimate

st.set_page_config(page_title="Green-Ops SaaS", layout="wide")
st.title("🌿 AI-Driven Green-Ops for Cell Towers")

# Run the model
with st.spinner("Training model with live weather for Pimpri..."):
    try:
        historical_df, forecast, weather_df = train_and_predict()
        
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📈 Traffic Forecast (Next 48 Hours)")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=historical_df['ds'], y=historical_df['y'], name='Historical'))
            fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='Predicted'))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("⚡ Recommendations")
            st.dataframe(forecast[['ds', 'yhat', 'recommendation']].tail(10))
            
            savings = get_savings_estimate(forecast)
            st.metric("Estimated Savings", f"{savings}%")
            
    except Exception as e:
        st.error(f"Deployment Error: {e}")
        st.info("Ensure your requirements.txt pins pandas < 3.0.0")
