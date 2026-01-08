import pandas as pd
import streamlit as st

def demand_chart(df: pd.DataFrame):
    if df.empty:
        st.info("No demand data.")
        return
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    st.line_chart(df.set_index("datetime")[["nd"]])

def carbon_chart(df: pd.DataFrame):
    if df.empty:
        st.info("No carbon data.")
        return
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    st.line_chart(df.set_index("datetime")[["forecast"]])

