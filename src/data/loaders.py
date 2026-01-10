import streamlit as st
import pandas as pd
from datetime import datetime, date

# Supabase pagination settings
PAGE_SIZE = 1000

def _fetch_all_pages(_supabase, table: str, query_builder) -> list:
    """Fetch all pages of results from Supabase"""
    all_data = []
    offset = 0
    
    while True:
        resp = query_builder.range(offset, offset + PAGE_SIZE - 1).execute()
        if not resp.data:
            break
        all_data.extend(resp.data)
        if len(resp.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    
    return all_data

@st.cache_data(ttl=3600)
def fetch_date_bounds(_supabase) -> tuple[date, date]:
    """Fetch min and max dates available in the demand table"""
    if not _supabase:
        today = datetime.utcnow().date()
        return today, today
    
    # Get min date
    min_resp = (
        _supabase.table("historic_demand")
        .select("datetime")
        .order("datetime", desc=False)
        .limit(1)
        .execute()
    )
    # Get max date
    max_resp = (
        _supabase.table("historic_demand")
        .select("datetime")
        .order("datetime", desc=True)
        .limit(1)
        .execute()
    )
    
    today = datetime.utcnow().date()
    if min_resp.data and max_resp.data:
        min_date = datetime.fromisoformat(min_resp.data[0]["datetime"].replace("Z", "+00:00")).date()
        max_date = datetime.fromisoformat(max_resp.data[0]["datetime"].replace("Z", "+00:00")).date()
        return min_date, max_date
    return today, today

@st.cache_data(ttl=300)
def fetch_demand_range(_supabase, start: date, end: date) -> pd.DataFrame:
    if not _supabase:
        return pd.DataFrame()
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    
    query = (
        _supabase.table("historic_demand")
        .select("*")
        .gte("datetime", start_dt.isoformat())
        .lte("datetime", end_dt.isoformat())
        .order("datetime", desc=False)
    )
    data = _fetch_all_pages(_supabase, "historic_demand", query)
    return pd.DataFrame(data)

@st.cache_data(ttl=300)
def fetch_carbon_range(_supabase, start: date, end: date, regions: tuple) -> pd.DataFrame:
    """Fetch carbon intensity data. Regions must be a tuple for caching."""
    if not _supabase or not regions:
        return pd.DataFrame()
    regions_list = list(regions)
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    
    query = (
        _supabase.table("carbon_intensity")
        .select("*")
        .in_("region_name", regions_list)
        .gte("datetime", start_dt.isoformat())
        .lte("datetime", end_dt.isoformat())
        .order("datetime", desc=False)
    )
    data = _fetch_all_pages(_supabase, "carbon_intensity", query)
    return pd.DataFrame(data)

@st.cache_data(ttl=300)
def fetch_weather_range(_supabase, start: date, end: date, regions: tuple) -> pd.DataFrame:
    """Fetch weather data. Regions must be a tuple for caching."""
    if not _supabase or not regions:
        return pd.DataFrame()
    regions_list = list(regions)
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    
    query = (
        _supabase.table("weather")
        .select("*")
        .in_("region_name", regions_list)
        .gte("datetime", start_dt.isoformat())
        .lte("datetime", end_dt.isoformat())
        .order("datetime", desc=False)
    )
    data = _fetch_all_pages(_supabase, "weather", query)
    return pd.DataFrame(data)
