import streamlit as st
from datetime import datetime, timedelta, date

# Sub-regions grouped by country
ENGLAND_REGIONS = ["North West England", "North East England", "South Yorkshire", 
                   "West Midlands", "East Midlands", "East England",
                   "South West England", "South England", "London", "South East England"]
WALES_REGIONS = ["North Wales & Merseyside", "South Wales"]
SCOTLAND_REGIONS = ["North Scotland", "South Scotland"]

# All sub-regions
REGIONS = SCOTLAND_REGIONS + WALES_REGIONS + ENGLAND_REGIONS

# Country-level options
COUNTRIES = ["England", "Wales", "Scotland"]

# Mapping from country to sub-regions
COUNTRY_TO_REGIONS = {
    "England": ENGLAND_REGIONS,
    "Wales": WALES_REGIONS,
    "Scotland": SCOTLAND_REGIONS
}

def render_sidebar(supabase, min_date: date, max_date: date):
    """Render sidebar controls and return selected parameters"""
    with st.sidebar:
        st.subheader("Controls")
        st.caption(f"Data available: {min_date} to {max_date}")
        
        # Date range selector
        date_mode = st.radio("Date Selection", ["Single Day", "Date Range", "Quick Select"], key="date_mode")
        
        if date_mode == "Single Day":
            start_date = st.date_input("Date", max_date, min_value=min_date, max_value=max_date, key="single_date")
            end_date = start_date
        elif date_mode == "Date Range":
            col1, col2 = st.columns(2)
            with col1:
                default_start = max(min_date, max_date - timedelta(days=7))
                start_date = st.date_input("Start", default_start, min_value=min_date, max_value=max_date, key="range_start")
            with col2:
                end_date = st.date_input("End", max_date, min_value=min_date, max_value=max_date, key="range_end")
            # Ensure start <= end
            if start_date > end_date:
                start_date, end_date = end_date, start_date
        else:  # Quick Select
            quick = st.selectbox("Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All available"], key="quick_period")
            if quick == "Last 7 days":
                end_date = max_date
                start_date = max(min_date, end_date - timedelta(days=7))
            elif quick == "Last 30 days":
                end_date = max_date
                start_date = max(min_date, end_date - timedelta(days=30))
            elif quick == "Last 90 days":
                end_date = max_date
                start_date = max(min_date, end_date - timedelta(days=90))
            else:  # All available
                start_date = min_date
                end_date = max_date
        
        # Show selected date range for confirmation
        days_selected = (end_date - start_date).days + 1
        st.success(f"Selected: {start_date} to {end_date} ({days_selected} days)")
        
        st.divider()
        
        # Region selector defaults to 'Single Region' with first region as default
        region_mode = st.radio("Region Selection", ["Single Region", "Country", "Multiple Regions", "All Regions"], key="region_mode", index=0)

        if region_mode == "Country":
            selected_country = st.selectbox("Country", COUNTRIES, key="country_select")
            selected_regions = COUNTRY_TO_REGIONS[selected_country]
            st.caption(f"Includes: {', '.join(selected_regions)}")
        elif region_mode == "Single Region":
            selected_regions = [st.selectbox("Region", REGIONS, key="single_region", index=0)]
        elif region_mode == "Multiple Regions":
            selected_regions = st.multiselect("Regions", REGIONS, default=[REGIONS[0]], key="multi_regions")
        else:  # All Regions
            selected_regions = REGIONS
        
        st.divider()
        st.text(f"Supabase: {'OK' if supabase else 'Missing'}")
        st.text(f"Regions: {len(selected_regions)}")
    
    return start_date, end_date, selected_regions
