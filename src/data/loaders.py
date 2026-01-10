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

def _get_table_min_max(_supabase, table: str) -> tuple[date | None, date | None]:
    """Return (min_date, max_date) for table datetime column, or (None, None) if unavailable."""
    try:
        min_resp = (
            _supabase.table(table)
            .select("datetime")
            .order("datetime", desc=False)
            .limit(1)
            .execute()
        )
        max_resp = (
            _supabase.table(table)
            .select("datetime")
            .order("datetime", desc=True)
            .limit(1)
            .execute()
        )
        if not (min_resp.data and max_resp.data):
            return None, None
        # Handle TIMESTAMP/TIMESTAMPTZ with or without trailing Z
        def _to_date(val: str) -> date:
            s = val if isinstance(val, str) else str(val)
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s).date()
        return _to_date(min_resp.data[0]["datetime"]), _to_date(max_resp.data[0]["datetime"])
    except Exception:
        return None, None

@st.cache_data(ttl=3600)
def fetch_date_bounds(_supabase) -> tuple[date, date]:
    """Return the overlapping date range where demand, carbon, and weather all have data."""
    today = datetime.utcnow().date()
    if not _supabase:
        return today, today

    d_min, d_max = _get_table_min_max(_supabase, "historic_demand")
    c_min, c_max = _get_table_min_max(_supabase, "carbon_intensity")
    w_min, w_max = _get_table_min_max(_supabase, "weather")

    mins = [m for m in [d_min, c_min, w_min] if m is not None]
    maxs = [m for m in [d_max, c_max, w_max] if m is not None]

    if not mins or not maxs:
        return today, today

    # Intersection: start = max(mins), end = min(maxs)
    start = max(mins)
    end = min(maxs)

    # If intersection is empty or inverted, fallback to today
    if start > end:
        return today, today
    return start, end

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
