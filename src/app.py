import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from supabase_client import get_supabase
from charts import demand_chart, carbon_chart

load_dotenv()
supabase = get_supabase()

st.set_page_config(page_title="Energy Dashboard", layout="wide")
st.title("Energy Dashboard")
st.caption(f"Last refreshed: {datetime.utcnow():%Y-%m-%d %H:%M UTC}")

with st.sidebar:
    st.subheader("Controls")
    selected_date: date = st.date_input("Date", datetime.utcnow().date())
    region = st.selectbox("Region", ["North Scotland", "South Scotland", "North West England",
                                     "North East England", "South Yorkshire", "North Wales & Merseyside",
                                     "South Wales", "West Midlands", "East Midlands", "East England",
                                     "South West England", "South England", "London", "South East England"])
    st.divider()
    st.text(f"Supabase: {'OK' if supabase else 'Missing'}")

@st.cache_data(ttl=300)
def fetch_demand_for_date(day: date) -> pd.DataFrame:
    if not supabase:
        return pd.DataFrame()
    start_dt = datetime.combine(day, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)
    resp = (
        supabase.table("historic_demand")
        .select("*")
        .gte("datetime", start_dt.isoformat())
        .lt("datetime", end_dt.isoformat())
        .order("datetime", desc=False)
        .limit(2000)
        .execute()
    )
    return pd.DataFrame(resp.data or [])

@st.cache_data(ttl=300)
def fetch_carbon_for_date(day: date, region_name: str) -> pd.DataFrame:
    if not supabase:
        return pd.DataFrame()
    start_dt = datetime.combine(day, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)
    resp = (
        supabase.table("carbon_intensity")
        .select("*")
        .eq("region_name", region_name)
        .gte("datetime", start_dt.isoformat())
        .lt("datetime", end_dt.isoformat())
        .order("datetime", desc=False)
        .limit(2000)
        .execute()
    )
    return pd.DataFrame(resp.data or [])

@st.cache_data(ttl=300)
def fetch_weather_for_date(day: date, region_name: str) -> pd.DataFrame:
    if not supabase:
        return pd.DataFrame()
    start_dt = datetime.combine(day, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)
    resp = (
        supabase.table("weather")
        .select("*")
        .eq("region_name", region_name)
        .gte("datetime", start_dt.isoformat())
        .lt("datetime", end_dt.isoformat())
        .order("datetime", desc=False)
        .limit(2500)
        .execute()
    )
    return pd.DataFrame(resp.data or [])

demand_df = fetch_demand_for_date(selected_date)
carbon_df = fetch_carbon_for_date(selected_date, region)
weather_df = fetch_weather_for_date(selected_date, region)

tab1, tab2, tab3 = st.tabs(["Summary", "Demand & Carbon", "Weather"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        if not demand_df.empty:
            latest = demand_df.sort_values("datetime").iloc[-1]
            st.metric("Demand (MW)", f"{latest.get('nd', 0):,.0f}")
        else:
            st.metric("Demand (MW)", "—")
    with col2:
        if not carbon_df.empty:
            latest_c = carbon_df.sort_values("datetime").iloc[-1]
            st.metric("Carbon Intensity", f"{latest_c.get('forecast', 0):,.0f} gCO₂/kWh")
        else:
            st.metric("Carbon Intensity", "—")
    with col3:
        if not weather_df.empty:
            latest_w = weather_df.sort_values("datetime").iloc[-1]
            st.metric("Temp (°C)", f"{latest_w.get('temperature', 0):.1f}")
        else:
            st.metric("Temp (°C)", "—")

with tab2:
    demand_chart(demand_df)
    carbon_chart(carbon_df)

with tab3:
    if weather_df.empty:
        st.info("No weather data for this date/region.")
    else:
        wdf = weather_df.copy()
        wdf["datetime"] = pd.to_datetime(wdf["datetime"])
        st.line_chart(wdf.set_index("datetime")[["temperature", "wind_speed", "humidity"]])
        st.line_chart(wdf.set_index("datetime")[["cloud_cover", "precipitation"]])