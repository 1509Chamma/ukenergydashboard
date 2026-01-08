import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Energy Dashboard", layout="wide")

st.title("Energy Dashboard")
st.caption(f"Last refreshed: {datetime.now()}")

with st.sidebar:
    st.subheader("Controls")
    date = st.date_input("Date", datetime.utcnow().date())
    region = st.selectbox("Region", ["North", "South", "East", "West"])

tab1, tab2 = st.tabs(["Summary", "Chart"])

with tab1:
    st.metric("Sample Demand", "34,200 MW", "+1.2% vs prev")
    st.metric("Sample Carbon Intensity", "165 gCO₂/kWh", "-3.1% vs prev")

with tab2:
    df = pd.DataFrame({
        "time": pd.date_range(datetime.now().replace(hour=0, minute=0), periods=24, freq="H"),
        "demand": [32000 + i * 50 for i in range(24)]
    })
    st.line_chart(df.set_index("time"))