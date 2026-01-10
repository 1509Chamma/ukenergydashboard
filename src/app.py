import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase_client import get_supabase
from data.loaders import fetch_demand_range, fetch_carbon_range, fetch_weather_range, fetch_date_bounds
from components.sidebar import render_sidebar
from components.charts import demand_chart, carbon_chart, weather_charts, summary_kpis, multi_series_chart

load_dotenv()

# Initialize session state
if "focus_metric" not in st.session_state:
    st.session_state.focus_metric = None
if "active_timerange" not in st.session_state:
    st.session_state.active_timerange = None
supabase = get_supabase()

st.set_page_config(page_title="Energy Dashboard", layout="wide")
st.title("Energy Dashboard")
st.caption(f"Last refreshed: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")

# Fetch available date bounds
min_date, max_date = fetch_date_bounds(supabase)

# Render sidebar and get parameters
start_date, end_date, selected_regions = render_sidebar(supabase, min_date, max_date)

# Fetch data only if regions are selected
if selected_regions:
    # Convert regions to tuple for proper caching
    regions_tuple = tuple(selected_regions)
    demand_df = fetch_demand_range(supabase, start_date, end_date)
    carbon_df = fetch_carbon_range(supabase, start_date, end_date, regions_tuple)
    weather_df = fetch_weather_range(supabase, start_date, end_date, regions_tuple)
else:
    import pandas as pd
    demand_df = pd.DataFrame()
    carbon_df = pd.DataFrame()
    weather_df = pd.DataFrame()
    st.warning("Please select at least one region to view data.")

# Tabs
tab1, tab2, tab3 = st.tabs(["Summary", "Demand & Carbon", "Weather"])

with tab1:
    summary_kpis(demand_df, carbon_df, weather_df)
    
    # Multi-series time chart with range brushing
    st.divider()
    multi_series_chart(demand_df, carbon_df, weather_df, focus_metric=st.session_state.focus_metric)
    
    # Show current focus
    if st.session_state.focus_metric:
        st.info(f"Focused metric: **{st.session_state.focus_metric.title()}** - This metric is emphasized in charts below. Click again to clear.")

with tab2:
    focus = st.session_state.focus_metric
    
    # Show demand chart (emphasized if focused)
    st.subheader("National Demand" + (" (Focused)" if focus == "demand" else ""))
    demand_chart(demand_df, start_date, end_date, emphasized=(focus == "demand"))
    
    # Show carbon chart (emphasized if focused)
    st.subheader("Carbon Intensity by Region" + (" (Focused)" if focus == "carbon" else ""))
    carbon_chart(carbon_df, selected_regions, start_date, end_date, emphasized=(focus == "carbon"))

with tab3:
    weather_charts(weather_df, selected_regions, start_date, end_date, focus_metric=st.session_state.focus_metric)