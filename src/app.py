import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase_client import get_supabase
from data.loaders import fetch_demand_range, fetch_carbon_range, fetch_weather_range, fetch_date_bounds
from components.sidebar import render_sidebar
from components.charts import demand_chart, carbon_chart, weather_charts, summary_kpis, multi_series_chart, uk_carbon_map, explanatory_summary

load_dotenv()

# Initialize session state
if "focus_metric" not in st.session_state:
    st.session_state.focus_metric = None
if "active_timerange" not in st.session_state:
    st.session_state.active_timerange = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0
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

# Custom persistent tabs
TAB_NAMES = ["Summary", "Demand & Carbon", "Weather"]

# Create tab-like buttons with CSS styling to match native tabs
st.markdown("""
<style>
/* Container for custom tabs */
div[data-testid="stHorizontalBlock"]:has(> div > div > div > div > button) {
    gap: 0.5rem !important;
    border-bottom: none !important;
    padding-bottom: 0;
    align-items: flex-end !important;
    margin-bottom: 1rem;
}
/* All tab buttons */
div.stButton > button {
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0.5rem 1rem !important;
    margin: 0 !important;
    color: #808495 !important;
    font-weight: 400 !important;
    font-size: 0.875rem !important;
    min-height: 0 !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    width: auto !important;
    min-width: fit-content !important;
}
div.stButton > button:hover {
    color: #fafafa !important;
    background-color: transparent !important;
}
/* Remove extra spacing */
div.stButton {
    margin-bottom: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Tab buttons in columns - wider for "Demand & Carbon"
tab_cols = st.columns([1, 1.8, 1, 6])  # 3 tabs + spacer
for i, tab_name in enumerate(TAB_NAMES):
    with tab_cols[i]:
        if st.button(tab_name, key=f"tab_{i}"):
            st.session_state.active_tab = i
            st.rerun()
        # Add colored underline based on active state
        if st.session_state.active_tab == i:
            st.markdown('<div style="height:2px;background-color:#ff4b4b;margin-top:-10px;margin-left:15px;margin-right:15px;"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="height:2px;background-color:#333;margin-top:-10px;margin-left:15px;margin-right:15px;"></div>', unsafe_allow_html=True)

# Render content based on active tab
if st.session_state.active_tab == 0:  # Summary
    summary_kpis(demand_df, carbon_df, weather_df)
    
    # Explanatory insights panel
    explanatory_summary(demand_df, carbon_df, weather_df, focus_metric=st.session_state.focus_metric)
    
    # Multi-series time chart with range brushing
    st.divider()
    multi_series_chart(demand_df, carbon_df, weather_df, focus_metric=st.session_state.focus_metric)
    
    # Show current focus
    if st.session_state.focus_metric:
        st.info(f"Focused metric: **{st.session_state.focus_metric.title()}** - This metric is emphasized in charts below. Click again to clear.")

elif st.session_state.active_tab == 1:  # Demand & Carbon
    st.subheader("UK Carbon Intensity Map")
    uk_carbon_map(carbon_df, demand_df)

elif st.session_state.active_tab == 2:  # Weather
    weather_charts(weather_df, selected_regions, start_date, end_date, focus_metric=st.session_state.focus_metric)