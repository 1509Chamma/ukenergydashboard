from datetime import datetime, timedelta, date
import pandas as pd
import streamlit as st

@st.cache_data(ttl=300)
def fetch_demand_for_date(supabase, day: date) -> pd.DataFrame:
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
def fetch_carbon_for_date(supabase, day: date) -> pd.DataFrame:
    if not supabase:
        return pd.DataFrame()
    start_dt = datetime.combine(day, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)
    resp = (
        supabase.table("carbon_intensity")
        .select("*")
        .gte("datetime", start_dt.isoformat())
        .lt("datetime", end_dt.isoformat())
        .order("datetime", desc=False)
        .limit(5000)
        .execute()
    )
    return pd.DataFrame(resp.data or [])

@st.cache_data(ttl=300)
def fetch_flights_trino(trino, day: date) -> pd.DataFrame:
    if not trino:
        return pd.DataFrame()
    start_dt = datetime.combine(day, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)
    try:
        flights = trino.flightlist(start=start_dt, end=end_dt)
        return pd.DataFrame(flights)
    except Exception:
        return pd.DataFrame()