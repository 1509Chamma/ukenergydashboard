import streamlit as st
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase_client import get_supabase
from data.loaders import fetch_demand_range, fetch_carbon_range, fetch_weather_range, fetch_date_bounds, should_run_update
from components.sidebar import render_sidebar
from components.charts import demand_chart, carbon_chart, weather_charts, summary_kpis, multi_series_chart, uk_carbon_map, explanatory_summary, uk_import_dependency, carbon_heatmap, generation_mix_stacked_bar
from data_update import update_and_upload_carbon_data, update_and_upload_weather_data, update_and_upload_demand_data
from components.time_series_experimentation import render_time_series_experimentation

load_dotenv()

# Background data update (non-blocking, once per day)
def _run_data_updates():
    try:
        update_and_upload_carbon_data()
    except Exception as e:
        print(f"Background: Could not update carbon data: {str(e)}")
    try:
        update_and_upload_weather_data()
    except Exception as e:
        print(f"Background: Could not update weather data: {str(e)}")
    try:
        update_and_upload_demand_data()
    except Exception as e:
        print(f"Background: Could not update demand data: {str(e)}")

if "data_update_started" not in st.session_state:
    st.session_state.data_update_started = False
    st.session_state.data_update_thread = None
    st.session_state.data_update_applied = False

supabase = get_supabase()

# Only run update if 24 hours have passed since last update (global check)
if not st.session_state.data_update_started and should_run_update(supabase, hours_interval=24):
    st.session_state.data_update_thread = threading.Thread(target=_run_data_updates, daemon=True)
    st.session_state.data_update_thread.start()
    st.session_state.data_update_started = True

# Show a small notice if background update is running
if st.session_state.data_update_thread and st.session_state.data_update_thread.is_alive():
    st.info("Updating data in background… You can continue using the app.")
else:
    # If finished and not yet applied, clear caches and rerun to pick up new data
    if st.session_state.data_update_started and not st.session_state.data_update_applied:
        try:
            st.cache_data.clear()
        except Exception:
            pass
        st.session_state.data_update_applied = True
        st.success("Data update complete. Refreshing…")
        st.rerun()

# Track selection changes and queue while background update runs
if "last_selected_regions" not in st.session_state:
    st.session_state.last_selected_regions = None
if "last_start_date" not in st.session_state:
    st.session_state.last_start_date = None
if "last_end_date" not in st.session_state:
    st.session_state.last_end_date = None
if "queued_selection" not in st.session_state:
    st.session_state.queued_selection = None

# Initialize session state
if "focus_metric" not in st.session_state:
    st.session_state.focus_metric = None
if "active_timerange" not in st.session_state:
    st.session_state.active_timerange = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

st.set_page_config(page_title="Energy Dashboard", layout="wide")
st.title("Energy Dashboard")
st.caption(f"Last refreshed: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")

# Fetch available date bounds
min_date, max_date = fetch_date_bounds(supabase)

# Render sidebar and get parameters
start_date, end_date, selected_regions = render_sidebar(supabase, min_date, max_date)

# Determine if selection changed
selection_changed = (
    st.session_state.last_selected_regions is not None and (
        selected_regions != st.session_state.last_selected_regions or
        start_date != st.session_state.last_start_date or
        end_date != st.session_state.last_end_date
    )
)

# If background update is running and selection changed, queue it and use last selection
use_previous = False
if st.session_state.data_update_thread and st.session_state.data_update_thread.is_alive() and selection_changed:
    st.session_state.queued_selection = {
        "regions": selected_regions,
        "start": start_date,
        "end": end_date,
    }
    st.info("New selection queued while data updates. It will refresh automatically when ready.")
    use_previous = True

# Effective selection to use for fetch
effective_regions = selected_regions
effective_start = start_date
effective_end = end_date

if use_previous and st.session_state.last_selected_regions:
    effective_regions = st.session_state.last_selected_regions
    effective_start = st.session_state.last_start_date or start_date
    effective_end = st.session_state.last_end_date or end_date

# Update last selection if not queued
if not use_previous:
    st.session_state.last_selected_regions = selected_regions
    st.session_state.last_start_date = start_date
    st.session_state.last_end_date = end_date

# Fetch data only if regions are selected
if effective_regions:
    # Convert regions to tuple for proper caching
    regions_tuple = tuple(effective_regions)
    demand_df = fetch_demand_range(supabase, effective_start, effective_end)
    carbon_df = fetch_carbon_range(supabase, effective_start, effective_end, regions_tuple)
    weather_df = fetch_weather_range(supabase, effective_start, effective_end, regions_tuple)
else:
    import pandas as pd
    demand_df = pd.DataFrame()
    carbon_df = pd.DataFrame()
    weather_df = pd.DataFrame()
    st.warning("Please select at least one region to view data.")

# Custom persistent tabs
TAB_NAMES = ["Summary", "Demand & Carbon", "Weather", "Experimentation"]

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
tab_cols = st.columns([1, 1.8, 1, 1.5, 5])  # 4 tabs + spacer
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
    
    st.divider()
    st.subheader("Carbon Intensity Patterns")
    carbon_heatmap(carbon_df)
    
    st.divider()
    st.subheader("Generation Mix: Renewable vs Non-Renewable")
    generation_mix_stacked_bar(carbon_df)
    st.divider()
    st.subheader("UK Import Dependency")
    uk_import_dependency(demand_df)

elif st.session_state.active_tab == 2:  # Weather
    from components.charts import render_weather_energy_relevance, exploratory_scatter_plot
    weather_charts(weather_df, selected_regions, start_date, end_date, focus_metric=st.session_state.focus_metric)
    st.divider()
    st.markdown("<h3 style='margin-bottom:0.5rem;'>Weather → Energy Relevance</h3>", unsafe_allow_html=True)
    render_weather_energy_relevance(weather_df)
    st.divider()
    st.markdown("<h3 style='margin-bottom:0.5rem;'>Weather/Energy Exploratory Scatter Plot</h3>", unsafe_allow_html=True)
    exploratory_scatter_plot(weather_df, demand_df, carbon_df)

elif st.session_state.active_tab == 3:  # Experimentation
    try:
        render_time_series_experimentation(supabase, min_date, max_date)
    except ImportError as e:
        st.error(f"Failed to import experimentation module: {e}")
    except Exception as e:
        st.error(f"Error in experimentation tab: {e}")
        import traceback
        st.write(traceback.format_exc())