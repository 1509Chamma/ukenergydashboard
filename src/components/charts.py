import pandas as pd
import streamlit as st
import altair as alt
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

def _create_sparkline(df: pd.DataFrame, x_col: str, y_col: str, color: str) -> alt.Chart:
    """Create a consistent sparkline chart"""
    return alt.Chart(df).mark_area(
        line={"color": color},
        color=alt.Gradient(gradient="linear", stops=[
            alt.GradientStop(color=color, offset=0),
            alt.GradientStop(color=f"{color}1A", offset=1)  # 10% opacity
        ], x1=1, x2=1, y1=1, y2=0)
    ).encode(
        x=alt.X(f"{x_col}:T", axis=None),
        y=alt.Y(f"{y_col}:Q", axis=None, scale=alt.Scale(zero=False))
    ).properties(height=60)


def _metric_button(label: str, metric_key: str) -> bool:
    """Create a clickable header that sets focus_metric"""
    is_focused = st.session_state.get("focus_metric") == metric_key
    if st.button(f"{'> ' if is_focused else ''}{label}", key=f"btn_{metric_key}", use_container_width=True):
        st.session_state.focus_metric = metric_key if st.session_state.get("focus_metric") != metric_key else None
        st.rerun()
    return is_focused


def multi_series_chart(demand_df: pd.DataFrame, carbon_df: pd.DataFrame, weather_df: pd.DataFrame, focus_metric: str = None):
    """Plotly multi-series time chart with range brushing. Stores selection in session_state.active_timerange."""
    
    fig = go.Figure()
    
    # Prepare data - normalize to common datetime index
    series_added = False
    
    # Demand series
    if not demand_df.empty and "nd" in demand_df.columns:
        demand_plot = demand_df.copy()
        demand_plot["datetime"] = pd.to_datetime(demand_plot["datetime"])
        # Normalize demand to 0-100 scale for comparison
        d_min, d_max = demand_plot["nd"].min(), demand_plot["nd"].max()
        demand_plot["nd_norm"] = (demand_plot["nd"] - d_min) / (d_max - d_min) * 100 if d_max > d_min else 50
        
        is_focused = focus_metric == "demand"
        fig.add_trace(go.Scatter(
            x=demand_plot["datetime"],
            y=demand_plot["nd_norm"],
            mode="lines",
            name="Demand",
            line=dict(color="#1f77b4", width=3 if is_focused else 1.5),
            opacity=1.0 if is_focused or not focus_metric else 0.3,
            hovertemplate="Demand: %{customdata:,.0f} MW<extra></extra>",
            customdata=demand_plot["nd"]
        ))
        series_added = True
    
    # Carbon series (aggregate across regions)
    if not carbon_df.empty and "forecast" in carbon_df.columns:
        carbon_plot = carbon_df.groupby("datetime")["forecast"].mean().reset_index()
        carbon_plot["datetime"] = pd.to_datetime(carbon_plot["datetime"])
        c_min, c_max = carbon_plot["forecast"].min(), carbon_plot["forecast"].max()
        carbon_plot["carbon_norm"] = (carbon_plot["forecast"] - c_min) / (c_max - c_min) * 100 if c_max > c_min else 50
        
        is_focused = focus_metric == "carbon"
        fig.add_trace(go.Scatter(
            x=carbon_plot["datetime"],
            y=carbon_plot["carbon_norm"],
            mode="lines",
            name="Carbon",
            line=dict(color="#2ca02c", width=3 if is_focused else 1.5),
            opacity=1.0 if is_focused or not focus_metric else 0.3,
            hovertemplate="Carbon: %{customdata:.0f} g/kWh<extra></extra>",
            customdata=carbon_plot["forecast"]
        ))
        series_added = True
    
    # Temperature series (aggregate across regions)
    if not weather_df.empty and "temperature" in weather_df.columns:
        temp_plot = weather_df.groupby("datetime")["temperature"].mean().reset_index()
        temp_plot["datetime"] = pd.to_datetime(temp_plot["datetime"])
        t_min, t_max = temp_plot["temperature"].min(), temp_plot["temperature"].max()
        temp_plot["temp_norm"] = (temp_plot["temperature"] - t_min) / (t_max - t_min) * 100 if t_max > t_min else 50
        
        is_focused = focus_metric == "temperature"
        fig.add_trace(go.Scatter(
            x=temp_plot["datetime"],
            y=temp_plot["temp_norm"],
            mode="lines",
            name="Temperature",
            line=dict(color="#d62728", width=3 if is_focused else 1.5),
            opacity=1.0 if is_focused or not focus_metric else 0.3,
            hovertemplate="Temp: %{customdata:.1f}C<extra></extra>",
            customdata=temp_plot["temperature"]
        ))
        series_added = True
    
    # Wind series (aggregate across regions)
    if not weather_df.empty and "wind_speed" in weather_df.columns:
        wind_plot = weather_df.groupby("datetime")["wind_speed"].mean().reset_index()
        wind_plot["datetime"] = pd.to_datetime(wind_plot["datetime"])
        w_min, w_max = wind_plot["wind_speed"].min(), wind_plot["wind_speed"].max()
        wind_plot["wind_norm"] = (wind_plot["wind_speed"] - w_min) / (w_max - w_min) * 100 if w_max > w_min else 50
        
        is_focused = focus_metric == "wind"
        fig.add_trace(go.Scatter(
            x=wind_plot["datetime"],
            y=wind_plot["wind_norm"],
            mode="lines",
            name="Wind",
            line=dict(color="#9467bd", width=3 if is_focused else 1.5),
            opacity=1.0 if is_focused or not focus_metric else 0.3,
            hovertemplate="Wind: %{customdata:.1f} m/s<extra></extra>",
            customdata=wind_plot["wind_speed"]
        ))
        series_added = True
    
    if not series_added:
        st.info("No data available for multi-series chart.")
        return
    
    # Calculate data range to determine which buttons should be available
    all_dates = []
    if not demand_df.empty and "datetime" in demand_df.columns:
        dates = pd.to_datetime(demand_df["datetime"]).dt.tz_localize(None)
        all_dates.extend(dates.tolist())
    if not carbon_df.empty and "datetime" in carbon_df.columns:
        dates = pd.to_datetime(carbon_df["datetime"]).dt.tz_localize(None)
        all_dates.extend(dates.tolist())
    if not weather_df.empty and "datetime" in weather_df.columns:
        dates = pd.to_datetime(weather_df["datetime"]).dt.tz_localize(None)
        all_dates.extend(dates.tolist())
    
    if all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)
        data_range_days = (max_date - min_date).days
    else:
        data_range_days = 0
    
    # Build buttons based on available data range
    range_buttons = []
    unavailable_ranges = []
    
    # 1 day - always available if we have any data
    if data_range_days >= 1:
        range_buttons.append(dict(count=1, label="1d", step="day", stepmode="backward"))
    else:
        unavailable_ranges.append("1d")
    
    # 1 week - need at least 7 days
    if data_range_days >= 7:
        range_buttons.append(dict(count=7, label="1w", step="day", stepmode="backward"))
    else:
        unavailable_ranges.append("1w")
    
    # 1 month - need at least 30 days
    if data_range_days >= 30:
        range_buttons.append(dict(count=1, label="1m", step="month", stepmode="backward"))
    else:
        unavailable_ranges.append("1m")
    
    # All - always available
    range_buttons.append(dict(step="all", label="All"))
    
    # Show warning if some ranges are unavailable
    if unavailable_ranges:
        st.caption(f"Range options unavailable (extend date range in sidebar): {', '.join(unavailable_ranges)}")
    
    # Configure layout with range selector - dark theme
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(color="#fafafa")
        ),
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.05, bgcolor="#1e1e1e"),
            rangeselector=dict(
                buttons=range_buttons,
                bgcolor="#262730",
                activecolor="#1f77b4",
                font=dict(color="#fafafa")
            ),
            type="date",
            gridcolor="#333333",
            color="#fafafa"
        ),
        yaxis=dict(
            title="Normalized (0-100)", 
            showgrid=True, 
            gridcolor="#333333",
            color="#fafafa"
        ),
        hovermode="x unified",
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#fafafa")
    )
    
    # Render chart and capture range selection
    chart_placeholder = st.empty()
    event = chart_placeholder.plotly_chart(
        fig, 
        use_container_width=True, 
        key="multi_series_chart",
        on_select="rerun",
        selection_mode="box"
    )
    
    # Store active time range from relayout event
    if event and hasattr(event, "selection") and event.selection:
        box = event.selection.get("box", [])
        if box and len(box) > 0:
            x_range = box[0].get("x", [])
            if len(x_range) >= 2:
                st.session_state.active_timerange = (x_range[0], x_range[1])
    
    # Show active time range if set
    if st.session_state.get("active_timerange"):
        start, end = st.session_state.active_timerange
        st.caption(f"Selected range: {start} to {end}")
        if st.button("Clear selection", key="clear_timerange"):
            st.session_state.active_timerange = None
            st.rerun()


def summary_kpis(demand_df: pd.DataFrame, carbon_df: pd.DataFrame, weather_df: pd.DataFrame):
    """Render enhanced summary KPIs with sparklines and deltas - clickable to set focus"""
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    # Demand KPIs
    with col1:
        _metric_button("Demand", "demand")
        if not demand_df.empty and "nd" in demand_df.columns:
            avg_demand = demand_df["nd"].mean()
            max_demand = demand_df["nd"].max()
            min_demand = demand_df["nd"].min()
            
            # Calculate trend (compare first half vs second half)
            mid = len(demand_df) // 2
            if mid > 0:
                first_half = demand_df["nd"].iloc[:mid].mean()
                second_half = demand_df["nd"].iloc[mid:].mean()
                delta = ((second_half - first_half) / first_half * 100) if first_half else 0
                help_text = f"Trend: First half avg {first_half:,.0f} MW → Second half avg {second_half:,.0f} MW"
                st.metric("Average", f"{avg_demand:,.0f} MW", f"{delta:+.1f}%", help=help_text)
            else:
                st.metric("Average", f"{avg_demand:,.0f} MW")
            
            st.metric("Peak", f"{max_demand:,.0f} MW")
            st.metric("Minimum", f"{min_demand:,.0f} MW")
            
            # Mini sparkline
            if len(demand_df) > 1:
                spark_df = demand_df[["datetime", "nd"]].copy()
                spark_df["datetime"] = pd.to_datetime(spark_df["datetime"])
                spark = _create_sparkline(spark_df, "datetime", "nd", "#1f77b4")
                st.altair_chart(spark, width="stretch")
        else:
            st.metric("Average", "—")
            st.metric("Peak", "—")
            st.metric("Minimum", "—")
    
    # Carbon KPIs
    with col2:
        _metric_button("Carbon", "carbon")
        if not carbon_df.empty and "forecast" in carbon_df.columns:
            # Aggregate by datetime for trend calculation
            carbon_agg = carbon_df.groupby("datetime")["forecast"].mean().reset_index()
            avg_carbon = carbon_agg["forecast"].mean()
            max_carbon = carbon_agg["forecast"].max()
            min_carbon = carbon_agg["forecast"].min()
            
            # Carbon intensity rating
            if avg_carbon < 150:
                rating_text = "Low"
            elif avg_carbon < 250:
                rating_text = "Moderate"
            else:
                rating_text = "High"
            
            # Calculate trend (first half vs second half)
            mid = len(carbon_agg) // 2
            if mid > 0:
                first_half = carbon_agg["forecast"].iloc[:mid].mean()
                second_half = carbon_agg["forecast"].iloc[mid:].mean()
                delta = ((second_half - first_half) / first_half * 100) if first_half else 0
                help_text = f"Rating: {rating_text}. Trend: {first_half:,.0f} → {second_half:,.0f} g/kWh"
                st.metric("Average", f"{avg_carbon:,.0f} g/kWh", f"{delta:+.1f}%", delta_color="inverse", help=help_text)
            else:
                st.metric("Average", f"{avg_carbon:,.0f} g/kWh", help=f"Rating: {rating_text}")
            
            st.metric("Peak", f"{max_carbon:,.0f} g/kWh")
            st.metric("Minimum", f"{min_carbon:,.0f} g/kWh")
            
            # Mini sparkline
            if len(carbon_df) > 1:
                spark_df = carbon_df.groupby("datetime")["forecast"].mean().reset_index()
                spark_df["datetime"] = pd.to_datetime(spark_df["datetime"])
                spark = _create_sparkline(spark_df, "datetime", "forecast", "#2ca02c")
                st.altair_chart(spark, width="stretch")
        else:
            st.metric("Average", "—")
            st.metric("Peak", "—")
            st.metric("Minimum", "—")
    
    # Temperature KPIs
    with col3:
        _metric_button("Temperature", "temperature")
        if not weather_df.empty and "temperature" in weather_df.columns:
            # Aggregate by datetime for trend calculation
            temp_agg = weather_df.groupby("datetime")["temperature"].mean().reset_index()
            avg_temp = temp_agg["temperature"].mean()
            max_temp = temp_agg["temperature"].max()
            min_temp = temp_agg["temperature"].min()
            
            # Calculate trend (first half vs second half)
            mid = len(temp_agg) // 2
            if mid > 0:
                first_half = temp_agg["temperature"].iloc[:mid].mean()
                second_half = temp_agg["temperature"].iloc[mid:].mean()
                delta = ((second_half - first_half) / abs(first_half) * 100) if first_half else 0
                help_text = f"Trend: First half avg {first_half:.1f}°C → Second half avg {second_half:.1f}°C"
                st.metric("Average", f"{avg_temp:.1f}°C", f"{delta:+.1f}%", help=help_text)
            else:
                st.metric("Average", f"{avg_temp:.1f}°C")
            
            st.metric("High", f"{max_temp:.1f}°C")
            st.metric("Low", f"{min_temp:.1f}°C")
            
            # Mini sparkline
            if len(weather_df) > 1:
                spark_df = weather_df.groupby("datetime")["temperature"].mean().reset_index()
                spark_df["datetime"] = pd.to_datetime(spark_df["datetime"])
                spark = _create_sparkline(spark_df, "datetime", "temperature", "#d62728")
                st.altair_chart(spark, width="stretch")
        else:
            st.metric("Average", "—")
            st.metric("High", "—")
            st.metric("Low", "—")
    
    # Wind KPIs
    with col4:
        _metric_button("Wind", "wind")
        if not weather_df.empty and "wind_speed" in weather_df.columns:
            # Aggregate by datetime for trend calculation
            wind_agg = weather_df.groupby("datetime")["wind_speed"].mean().reset_index()
            avg_wind = wind_agg["wind_speed"].mean()
            max_wind = wind_agg["wind_speed"].max()
            min_wind = wind_agg["wind_speed"].min()
            
            # Calculate trend (first half vs second half)
            mid = len(wind_agg) // 2
            if mid > 0:
                first_half = wind_agg["wind_speed"].iloc[:mid].mean()
                second_half = wind_agg["wind_speed"].iloc[mid:].mean()
                delta = ((second_half - first_half) / first_half * 100) if first_half else 0
                help_text = f"Trend: First half avg {first_half:.1f} m/s → Second half avg {second_half:.1f} m/s"
                st.metric("Average", f"{avg_wind:.1f} m/s", f"{delta:+.1f}%", help=help_text)
            else:
                st.metric("Average", f"{avg_wind:.1f} m/s")
            
            st.metric("Peak", f"{max_wind:.1f} m/s")
            st.metric("Minimum", f"{min_wind:.1f} m/s")
            
            # Mini sparkline for wind
            if len(weather_df) > 1:
                spark_df = weather_df.groupby("datetime")["wind_speed"].mean().reset_index()
                spark_df["datetime"] = pd.to_datetime(spark_df["datetime"])
                spark = _create_sparkline(spark_df, "datetime", "wind_speed", "#9467bd")
                st.altair_chart(spark, width="stretch")
        else:
            st.metric("Average", "—")
            st.metric("Peak", "—")
            st.metric("Minimum", "—")
    
    # Second row - Additional weather metrics
    st.divider()
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        if not weather_df.empty and "humidity" in weather_df.columns:
            avg_humidity = weather_df["humidity"].mean()
            st.metric("Humidity", f"{avg_humidity:.0f}%")
        else:
            st.metric("Humidity", "—")
    
    with col6:
        if not weather_df.empty and "cloud_cover" in weather_df.columns:
            avg_cloud = weather_df["cloud_cover"].mean()
            st.metric("Cloud Cover", f"{avg_cloud:.0f}%")
        else:
            st.metric("Cloud Cover", "—")
    
    with col7:
        if not weather_df.empty and "precipitation" in weather_df.columns:
            total_precip = weather_df["precipitation"].sum()
            st.metric("Total Precipitation", f"{total_precip:.1f} mm")
        else:
            st.metric("Total Precipitation", "—")
    
    with col8:
        # Data summary
        total_records = len(demand_df) + len(carbon_df) + len(weather_df)
        st.metric("Total Records", f"{total_records:,}")
        if not carbon_df.empty and "region_name" in carbon_df.columns:
            regions = carbon_df["region_name"].nunique()
            st.caption(f"{regions} regions selected")


def demand_chart(df: pd.DataFrame, start_date: date, end_date: date, emphasized: bool = False):
    if df.empty:
        st.info("No demand data.")
        return
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    
    # Create datetime bounds for chart
    x_min = datetime.combine(start_date, datetime.min.time())
    x_max = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
    
    # Emphasized styling
    stroke_width = 3 if emphasized else 2
    chart_height = 400 if emphasized else 300
    color = "#1f77b4"
    
    chart = alt.Chart(df).mark_line(strokeWidth=stroke_width, color=color).encode(
        x=alt.X("datetime:T", title="Time", scale=alt.Scale(domain=[x_min.isoformat(), x_max.isoformat()])),
        y=alt.Y("nd:Q", title="Demand (MW)"),
        tooltip=["datetime:T", "nd:Q"]
    ).interactive(bind_x=True, bind_y=False).properties(height=chart_height)
    
    st.altair_chart(chart, width="stretch")

def carbon_chart(df: pd.DataFrame, selected_regions: list, start_date: date, end_date: date, emphasized: bool = False):
    if df.empty:
        st.info("No carbon data.")
        return
    
    cdf = df.copy()
    cdf["datetime"] = pd.to_datetime(cdf["datetime"])
    
    # Create datetime bounds for chart
    x_min = datetime.combine(start_date, datetime.min.time())
    x_max = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
    
    # Emphasized styling
    stroke_width = 3 if emphasized else 2
    chart_height = 450 if emphasized else 350
    
    if len(selected_regions) > 1:
        chart = alt.Chart(cdf).mark_line(strokeWidth=stroke_width).encode(
            x=alt.X("datetime:T", title="Time", scale=alt.Scale(domain=[x_min.isoformat(), x_max.isoformat()])),
            y=alt.Y("forecast:Q", title="Carbon Intensity (gCO2/kWh)"),
            color=alt.Color("region_name:N", title="Region"),
            tooltip=["datetime:T", "region_name:N", "forecast:Q"]
        ).interactive(bind_x=True, bind_y=False).properties(height=chart_height)
    else:
        chart = alt.Chart(cdf).mark_line(strokeWidth=stroke_width).encode(
            x=alt.X("datetime:T", title="Time", scale=alt.Scale(domain=[x_min.isoformat(), x_max.isoformat()])),
            y=alt.Y("forecast:Q", title="Carbon Intensity (gCO2/kWh)"),
            tooltip=["datetime:T", "forecast:Q"]
        ).interactive(bind_x=True, bind_y=False).properties(height=chart_height - 50)
    
    st.altair_chart(chart, width="stretch")

def weather_charts(df: pd.DataFrame, selected_regions: list, start_date: date, end_date: date, focus_metric: str = None):
    if df.empty:
        st.info("No weather data for this date range/regions.")
        return
    
    wdf = df.copy()
    wdf["datetime"] = pd.to_datetime(wdf["datetime"])
    
    # Create datetime bounds for chart
    x_min = datetime.combine(start_date, datetime.min.time())
    x_max = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
    x_scale = alt.Scale(domain=[x_min.isoformat(), x_max.isoformat()])
    
    # Determine emphasis styling
    temp_emphasized = focus_metric == "temperature"
    wind_emphasized = focus_metric == "wind"
    temp_stroke = 4 if temp_emphasized else (1 if wind_emphasized else 2)
    wind_stroke = 4 if wind_emphasized else (1 if temp_emphasized else 2)
    temp_opacity = 1.0 if temp_emphasized or not focus_metric else 0.4
    wind_opacity = 1.0 if wind_emphasized or not focus_metric else 0.4
    chart_height = 400 if (temp_emphasized or wind_emphasized) else 300
    
    st.subheader("Temperature & Wind" + (" (Temperature Focused)" if temp_emphasized else " (Wind Focused)" if wind_emphasized else ""))
    if len(selected_regions) > 1:
        # Aggregate across regions
        agg_df = wdf.groupby("datetime").agg({"temperature": "mean", "wind_speed": "mean"}).reset_index()
        temp_chart = alt.Chart(agg_df).mark_line(color="red", strokeWidth=temp_stroke, opacity=temp_opacity).encode(
            x=alt.X("datetime:T", title="Time", scale=x_scale),
            y=alt.Y("temperature:Q", title="Temperature (C)"),
            tooltip=["datetime:T", "temperature:Q"]
        )
        wind_chart = alt.Chart(agg_df).mark_line(color="blue", strokeWidth=wind_stroke, opacity=wind_opacity).encode(
            x=alt.X("datetime:T", title="Time", scale=x_scale),
            y=alt.Y("wind_speed:Q", title="Wind Speed (m/s)"),
            tooltip=["datetime:T", "wind_speed:Q"]
        )
        combined = alt.layer(temp_chart, wind_chart).resolve_scale(y="independent").interactive(bind_x=True, bind_y=False).properties(height=chart_height)
        st.altair_chart(combined, width="stretch")
    else:
        base = alt.Chart(wdf).encode(x=alt.X("datetime:T", title="Time", scale=x_scale))
        temp_line = base.mark_line(color="red", strokeWidth=temp_stroke, opacity=temp_opacity).encode(y=alt.Y("temperature:Q", title="Temperature (C)"))
        wind_line = base.mark_line(color="blue", strokeWidth=wind_stroke, opacity=wind_opacity).encode(y=alt.Y("wind_speed:Q", title="Wind Speed (m/s)"))
        combined = alt.layer(temp_line, wind_line).resolve_scale(y="independent").interactive(bind_x=True, bind_y=False).properties(height=chart_height)
        st.altair_chart(combined, width="stretch")
    
    st.subheader("Cloud & Precipitation")
    if len(selected_regions) > 1:
        agg_df = wdf.groupby("datetime").agg({"cloud_cover": "mean", "precipitation": "mean"}).reset_index()
        cloud_chart = alt.Chart(agg_df).mark_line(color="gray").encode(
            x=alt.X("datetime:T", title="Time", scale=x_scale),
            y=alt.Y("cloud_cover:Q", title="Cloud Cover (%)"),
            tooltip=["datetime:T", "cloud_cover:Q"]
        )
        precip_chart = alt.Chart(agg_df).mark_line(color="teal").encode(
            x=alt.X("datetime:T", title="Time", scale=x_scale),
            y=alt.Y("precipitation:Q", title="Precipitation (mm)"),
            tooltip=["datetime:T", "precipitation:Q"]
        )
        combined = alt.layer(cloud_chart, precip_chart).resolve_scale(y="independent").interactive(bind_x=True, bind_y=False).properties(height=300)
        st.altair_chart(combined, width="stretch")
    else:
        base = alt.Chart(wdf).encode(x=alt.X("datetime:T", title="Time", scale=x_scale))
        cloud_line = base.mark_line(color="gray").encode(y=alt.Y("cloud_cover:Q", title="Cloud Cover (%)"))
        precip_line = base.mark_line(color="teal").encode(y=alt.Y("precipitation:Q", title="Precipitation (mm)"))
        combined = alt.layer(cloud_line, precip_line).resolve_scale(y="independent").interactive(bind_x=True, bind_y=False).properties(height=300)
        st.altair_chart(combined, width="stretch")

