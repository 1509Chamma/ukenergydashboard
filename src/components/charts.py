import pandas as pd
import streamlit as st
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta

# UK Region coordinates (approximate centers for each DNO region)
UK_REGION_COORDS = {
    "North Scotland": {"lat": 57.5, "lon": -4.5},
    "South Scotland": {"lat": 55.9, "lon": -3.7},
    "North East England": {"lat": 55.0, "lon": -1.6},
    "North West England": {"lat": 53.8, "lon": -2.5},
    "South Yorkshire": {"lat": 53.5, "lon": -1.2},
    "North Wales & Merseyside": {"lat": 53.2, "lon": -3.2},
    "South Wales": {"lat": 51.6, "lon": -3.4},
    "West Midlands": {"lat": 52.5, "lon": -2.0},
    "East Midlands": {"lat": 52.8, "lon": -0.8},
    "East England": {"lat": 52.2, "lon": 0.9},
    "South West England": {"lat": 50.7, "lon": -3.5},
    "South England": {"lat": 51.0, "lon": -1.3},
    "London": {"lat": 51.5, "lon": -0.1},
    "South East England": {"lat": 51.2, "lon": 0.5},
}


def explanatory_summary(demand_df: pd.DataFrame, carbon_df: pd.DataFrame, weather_df: pd.DataFrame, focus_metric: str = None):
    """Generate 3-5 bullet point insights based on filtered data and analysis focus"""
    
    insights = []
    
    # Demand insights
    if not demand_df.empty and "tsd" in demand_df.columns:
        avg_demand = demand_df["tsd"].mean()
        max_demand = demand_df["tsd"].max()
        min_demand = demand_df["tsd"].min()
        demand_range = max_demand - min_demand
        
        # Peak demand insight
        if "settlement_date" in demand_df.columns:
            peak_idx = demand_df["tsd"].idxmax()
            peak_time = demand_df.loc[peak_idx, "settlement_date"]
            if isinstance(peak_time, pd.Timestamp):
                insights.append(f"<strong>Peak demand</strong> of <strong>{max_demand:,.0f} MW</strong> occurred on {peak_time.strftime('%d %b %Y at %H:%M')}")
        
        # Demand variability
        if demand_range > 10000:
            insights.append(f"<strong>High demand variability</strong> observed — ranging from {min_demand:,.0f} MW to {max_demand:,.0f} MW (Δ {demand_range:,.0f} MW)")
        elif demand_range > 5000:
            insights.append(f"<strong>Moderate demand fluctuation</strong> — average of {avg_demand:,.0f} MW with {demand_range:,.0f} MW spread")
    
    # Carbon insights
    if not carbon_df.empty and "forecast" in carbon_df.columns:
        avg_carbon = carbon_df["forecast"].mean()
        carbon_rating = _get_carbon_rating(avg_carbon)
        
        # Regional comparison
        if "region_name" in carbon_df.columns:
            region_avg = carbon_df.groupby("region_name")["forecast"].mean()
            cleanest = region_avg.idxmin()
            dirtiest = region_avg.idxmax()
            
            if cleanest != dirtiest:
                insights.append(f"<strong>Cleanest region</strong>: {cleanest} ({region_avg[cleanest]:.0f} g/kWh) vs <strong>highest carbon</strong>: {dirtiest} ({region_avg[dirtiest]:.0f} g/kWh)")
        
        # Overall carbon rating
        insights.append(f"<strong>Average carbon intensity</strong>: {avg_carbon:.0f} g CO₂/kWh — rated <strong>{carbon_rating}</strong>")
    
    # Weather insights
    if not weather_df.empty:
        if "temperature" in weather_df.columns:
            avg_temp = weather_df["temperature"].mean()
            temp_trend = "mild" if 10 <= avg_temp <= 18 else ("cold" if avg_temp < 10 else "warm")
            insights.append(f"<strong>Weather conditions</strong> were {temp_trend} with average temperature of <strong>{avg_temp:.1f}°C</strong>")
        
        if "wind_speed" in weather_df.columns:
            avg_wind = weather_df["wind_speed"].mean()
            if avg_wind > 20:
                insights.append(f"<strong>Strong winds</strong> averaging {avg_wind:.1f} km/h — favourable for wind generation")
            elif avg_wind > 10:
                insights.append(f"<strong>Moderate winds</strong> at {avg_wind:.1f} km/h average")
    
    # Focus-specific insight
    if focus_metric:
        focus_insight = {
            "demand": "Currently focusing on <strong>demand patterns</strong> — click KPI cards to change focus",
            "carbon": "Currently focusing on <strong>carbon intensity</strong> — useful for identifying low-emission periods",
            "temperature": "Currently focusing on <strong>temperature</strong> — correlates with heating/cooling demand",
            "wind": "Currently focusing on <strong>wind speed</strong> — key driver for renewable generation"
        }
        if focus_metric in focus_insight:
            insights.append(focus_insight[focus_metric])
    
    # Ensure we have at least 3 insights
    if len(insights) < 3:
        if not demand_df.empty:
            days_span = (demand_df["settlement_date"].max() - demand_df["settlement_date"].min()).days if "settlement_date" in demand_df.columns else 0
            if days_span > 0:
                insights.append(f"Data spans <strong>{days_span} days</strong> of energy metrics")
    
    # Render as styled text panel
    if insights:
        # Build bullet list HTML
        bullets_html = "".join([f'<li style="margin-bottom: 0.5rem;">{insight}</li>' for insight in insights[:5]])
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 1.25rem 1.5rem; 
                    border-radius: 10px; 
                    border-left: 3px solid #ff4b4b;
                    margin: 1rem 0;">
            <h4 style="margin: 0 0 0.75rem 0; color: #fafafa; font-size: 1rem; font-weight: 600;">
                Key Insights
            </h4>
            <ul style="margin: 0; padding-left: 1.25rem; color: #e0e0e0; line-height: 1.6;">
                {bullets_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Select data filters to generate insights.")

def _get_carbon_color(intensity: float) -> str:
    """Get color based on carbon intensity severity"""
    if intensity < 100:
        return "#22c55e"  # Green - Very Low
    elif intensity < 150:
        return "#84cc16"  # Light Green - Low
    elif intensity < 200:
        return "#eab308"  # Yellow - Moderate
    elif intensity < 250:
        return "#f97316"  # Orange - High
    else:
        return "#ef4444"  # Red - Very High

def _get_carbon_rating(intensity: float) -> str:
    """Get rating text based on carbon intensity"""
    if intensity < 100:
        return "Very Low"
    elif intensity < 150:
        return "Low"
    elif intensity < 200:
        return "Moderate"
    elif intensity < 250:
        return "High"
    else:
        return "Very High"


def carbon_heatmap(carbon_df: pd.DataFrame):
    """Create an interactive heatmap showing carbon intensity by hour and day of week"""
    
    if carbon_df.empty:
        st.info("No carbon data available for the selected date range.")
        return
    
    # Ensure datetime column exists
    if "datetime" not in carbon_df.columns:
        st.warning("No datetime column found in carbon data.")
        return
    
    # Parse datetime and extract hour and weekday
    df = carbon_df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    
    # Check if we have more than 7 days of data
    date_range = (df["datetime"].max() - df["datetime"].min()).days
    if date_range < 7:
        st.info("Heatmap requires more than 7 days of data to show meaningful patterns. Please expand your date range.")
        return
    
    df["hour"] = df["datetime"].dt.hour
    df["weekday"] = df["datetime"].dt.dayofweek  # 0=Monday, 6=Sunday
    df["weekday_name"] = df["datetime"].dt.day_name()
    
    # Group by weekday and hour, calculate mean carbon intensity
    heatmap_data = df.groupby(["weekday", "hour"])["forecast"].mean().reset_index()
    heatmap_data.columns = ["weekday", "hour", "intensity"]
    
    # Pivot to 7x24 matrix
    pivot_df = heatmap_data.pivot(index="weekday", columns="hour", values="intensity")
    
    # Ensure all hours and weekdays are present
    pivot_df = pivot_df.reindex(index=range(7), columns=range(24))
    
    # Day names for Y-axis
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Create custom colorscale matching existing carbon colors
    # Very Low (0-100): Green, Low (100-150): Light Green, Moderate (150-200): Yellow, High (200-250): Orange, Very High (250+): Red
    carbon_colorscale = [
        [0.0, "#22c55e"],    # Very Low - Green
        [0.3, "#84cc16"],    # Low - Light Green
        [0.5, "#eab308"],    # Moderate - Yellow
        [0.7, "#f97316"],    # Orange - High
        [1.0, "#ef4444"],    # Very High - Red
    ]
    
    # Prepare hover text
    hover_text = []
    for weekday_idx in range(7):
        row_text = []
        for hour in range(24):
            val = pivot_df.loc[weekday_idx, hour] if pd.notna(pivot_df.loc[weekday_idx, hour]) else 0
            row_text.append(
                f"<b>{day_names[weekday_idx]}</b><br>"
                f"Hour: {hour:02d}:00<br>"
                f"Intensity: {val:.0f} gCO₂/kWh<br>"
                f"Rating: {_get_carbon_rating(val)}"
            )
        hover_text.append(row_text)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=[f"{h:02d}:00" for h in range(24)],
        y=day_names,
        colorscale=carbon_colorscale,
        hoverinfo="text",
        text=hover_text,
        colorbar=dict(
            title=dict(text="gCO₂/kWh", side="right"),
            tickvals=[50, 100, 150, 200, 250, 300],
            ticktext=["50", "100", "150", "200", "250", "300+"],
            len=0.9,
        ),
        zmin=0,
        zmax=300,
    ))
    
    fig.update_layout(
        title=dict(
            text="Carbon Intensity by Hour & Day of Week",
            x=0.5,
            font=dict(size=16)
        ),
        xaxis=dict(
            title="Hour of Day",
            tickmode="array",
            tickvals=[f"{h:02d}:00" for h in range(0, 24, 3)],
            ticktext=["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
            side="bottom",
            gridcolor="#333333",
        ),
        yaxis=dict(
            title="Day of Week",
            autorange="reversed",  # Monday at top
            gridcolor="#333333",
        ),
        height=400,
        margin=dict(l=100, r=20, t=50, b=60),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Add summary insights
    if not heatmap_data.empty:
        peak_row = heatmap_data.loc[heatmap_data["intensity"].idxmax()]
        low_row = heatmap_data.loc[heatmap_data["intensity"].idxmin()]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #ef4444;">
                <strong style="color: #ef4444;">⚠️ Peak Carbon</strong><br>
                <span style="color: #e0e0e0;">{day_names[int(peak_row['weekday'])]} at {int(peak_row['hour']):02d}:00 — {peak_row['intensity']:.0f} gCO₂/kWh</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #22c55e;">
                <strong style="color: #22c55e;">🌱 Lowest Carbon</strong><br>
                <span style="color: #e0e0e0;">{day_names[int(low_row['weekday'])]} at {int(low_row['hour']):02d}:00 — {low_row['intensity']:.0f} gCO₂/kWh</span>
            </div>
            """, unsafe_allow_html=True)


def uk_carbon_map(carbon_df: pd.DataFrame, demand_df: pd.DataFrame):
    """Create a UK map showing carbon intensity by region with demand summary"""
    
    if carbon_df.empty:
        st.info("No carbon data available for the selected date range and regions.")
        return
    
    # Calculate average carbon intensity per region
    region_avg = carbon_df.groupby("region_name")["forecast"].mean().reset_index()
    region_avg.columns = ["region", "intensity"]
    
    # Add coordinates
    region_avg["lat"] = region_avg["region"].map(lambda r: UK_REGION_COORDS.get(r, {}).get("lat"))
    region_avg["lon"] = region_avg["region"].map(lambda r: UK_REGION_COORDS.get(r, {}).get("lon"))
    region_avg["color"] = region_avg["intensity"].apply(_get_carbon_color)
    region_avg["rating"] = region_avg["intensity"].apply(_get_carbon_rating)
    
    # Filter out regions without coordinates
    region_avg = region_avg.dropna(subset=["lat", "lon"])
    
    if region_avg.empty:
        st.warning("No matching regions found for map display.")
        return
    
    # Create the map
    fig = go.Figure()
    
    # Add markers for each region
    for _, row in region_avg.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[row["lon"]],
            lat=[row["lat"]],
            mode="markers+text",
            marker=dict(
                size=45,
                color=row["color"],
                opacity=0.85,
                line=dict(width=2, color="#ffffff")
            ),
            text=f"{row['intensity']:.0f}",
            textposition="middle center",
            textfont=dict(size=11, color="white", family="Arial Black"),
            hovertemplate=(
                f"<b>{row['region']}</b><br>"
                f"Carbon: {row['intensity']:.0f} g/kWh<br>"
                f"Rating: {row['rating']}<extra></extra>"
            ),
            name=row["region"],
            showlegend=False
        ))
    
    # Configure map layout - dark theme UK focus
    fig.update_layout(
        geo=dict(
            scope="europe",
            projection_type="natural earth",
            center=dict(lat=54.5, lon=-2.5),
            lonaxis_range=[-8, 3],
            lataxis_range=[49, 59],
            bgcolor="#0e1117",
            landcolor="#1e1e2e",
            oceancolor="#0e1117",
            lakecolor="#0e1117",
            coastlinecolor="#333333",
            countrycolor="#333333",
            showland=True,
            showocean=True,
            showlakes=True,
            showcoastlines=True,
            showcountries=True,
        ),
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
        title=dict(
            text="Carbon Intensity by Region (g CO2/kWh)",
            x=0.5,
            font=dict(size=16)
        ),
        dragmode=False,  # Disable dragging/panning
    )
    
    # Disable scroll zoom and other interactions
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': False,
        'doubleClick': False,
        'displayModeBar': False
    })
    
    # Add legend/key below map
    st.markdown("**Intensity Scale:**")
    cols = st.columns(5)
    levels = [
        ("Very Low", "<100", "#22c55e"),
        ("Low", "100-149", "#84cc16"),
        ("Moderate", "150-199", "#eab308"),
        ("High", "200-249", "#f97316"),
        ("Very High", "250+", "#ef4444"),
    ]
    for col, (label, range_str, color) in zip(cols, levels):
        col.markdown(f"<div style='text-align:center;'><span style='background-color:{color}; padding:4px 12px; border-radius:4px; color:white; font-weight:bold;'>{range_str}</span><br><small>{label}</small></div>", unsafe_allow_html=True)
    
    # Show regional breakdown table
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Regional Carbon Intensity**")
        # Sort by intensity descending
        display_df = region_avg[["region", "intensity", "rating"]].sort_values("intensity", ascending=False)
        display_df.columns = ["Region", "Intensity (g/kWh)", "Rating"]
        display_df["Intensity (g/kWh)"] = display_df["Intensity (g/kWh)"].round(0).astype(int)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**National Demand Summary**")
        if not demand_df.empty and "nd" in demand_df.columns:
            avg_demand = demand_df["nd"].mean()
            max_demand = demand_df["nd"].max()
            min_demand = demand_df["nd"].min()
            latest_demand = demand_df["nd"].iloc[-1] if len(demand_df) > 0 else 0
            
            st.metric("Current", f"{latest_demand:,.0f} MW")
            st.metric("Average", f"{avg_demand:,.0f} MW")
            st.metric("Peak", f"{max_demand:,.0f} MW")
            st.metric("Minimum", f"{min_demand:,.0f} MW")
        else:
            st.info("No demand data available.")


# Interconnector metadata: name, country, color
INTERCONNECTORS = {
    "ifa_flow": {"name": "IFA", "country": "France", "color": "#0055A4"},
    "ifa2_flow": {"name": "IFA2", "country": "France", "color": "#0066CC"},
    "britned_flow": {"name": "BritNed", "country": "Netherlands", "color": "#FF6B00"},
    "moyle_flow": {"name": "Moyle", "country": "N. Ireland", "color": "#169B62"},
    "east_west_flow": {"name": "East-West", "country": "Ireland", "color": "#FF883E"},
    "nemo_flow": {"name": "NEMO", "country": "Belgium", "color": "#FDDA24"},
    "nsl_flow": {"name": "North Sea Link", "country": "Norway", "color": "#BA0C2F"},
    "eleclink_flow": {"name": "ElecLink", "country": "France", "color": "#3366CC"},
    "viking_flow": {"name": "Viking Link", "country": "Denmark", "color": "#C60C30"},
    "greenlink_flow": {"name": "Greenlink", "country": "Ireland", "color": "#22B14C"},
}


def uk_import_dependency(demand_df: pd.DataFrame):
    """Create visualization showing UK import/export dependency via interconnectors"""
    
    if demand_df.empty:
        st.info("No interconnector data available for the selected date range.")
        return
    
    # Find available interconnector columns
    flow_cols = [col for col in demand_df.columns if col in INTERCONNECTORS]
    
    if not flow_cols:
        st.warning("No interconnector flow data found in the dataset.")
        return
    
    # Calculate totals for each interconnector
    flow_summary = []
    for col in flow_cols:
        if col in demand_df.columns:
            total_flow = demand_df[col].sum()
            avg_flow = demand_df[col].mean()
            max_import = demand_df[col].max()
            max_export = demand_df[col].min()
            
            info = INTERCONNECTORS[col]
            flow_summary.append({
                "interconnector": info["name"],
                "country": info["country"],
                "color": info["color"],
                "total_gwh": total_flow / 2000,  # Convert MW half-hours to GWh
                "avg_mw": avg_flow,
                "max_import_mw": max_import,
                "max_export_mw": abs(max_export) if max_export < 0 else 0,
                "net_position": "Import" if total_flow > 0 else "Export"
            })
    
    flow_df = pd.DataFrame(flow_summary)
    
    if flow_df.empty:
        st.warning("No interconnector flow data available.")
        return
    
    # Calculate overall metrics
    total_import = flow_df[flow_df["total_gwh"] > 0]["total_gwh"].sum()
    total_export = abs(flow_df[flow_df["total_gwh"] < 0]["total_gwh"].sum())
    net_flow = total_import - total_export
    
    # Get demand for dependency calculation
    if "tsd" in demand_df.columns:
        total_demand_gwh = demand_df["tsd"].sum() / 2000
        dependency_pct = (net_flow / total_demand_gwh * 100) if total_demand_gwh > 0 else 0
    else:
        dependency_pct = 0
    
    # Summary KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Net Import", f"{net_flow:,.1f} GWh", 
                delta=f"{'Import' if net_flow > 0 else 'Export'}")
    col2.metric("Total Imported", f"{total_import:,.1f} GWh")
    col3.metric("Total Exported", f"{total_export:,.1f} GWh")
    col4.metric("Import Dependency", f"{dependency_pct:.1f}%",
                help="Net imports as percentage of total system demand")
    
    st.divider()
    
    # Create horizontal bar chart by country
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Aggregate by country for cleaner view
        country_flow = flow_df.groupby("country").agg({
            "total_gwh": "sum",
            "avg_mw": "sum",
            "color": "first"
        }).reset_index()
        country_flow = country_flow.sort_values("total_gwh", ascending=True)
        
        fig = go.Figure()
        
        for _, row in country_flow.iterrows():
            fig.add_trace(go.Bar(
                y=[row["country"]],
                x=[row["total_gwh"]],
                orientation="h",
                marker_color=row["color"] if row["total_gwh"] > 0 else "#888888",
                text=f"{row['total_gwh']:+.1f} GWh",
                textposition="auto",
                name=row["country"],
                showlegend=False,
                hovertemplate=f"<b>{row['country']}</b><br>" +
                              f"Net Flow: {row['total_gwh']:+.1f} GWh<br>" +
                              f"Avg: {row['avg_mw']:+.0f} MW<extra></extra>"
            ))
        
        fig.add_vline(x=0, line_dash="dash", line_color="#666666", line_width=1)
        
        fig.update_layout(
            title="Net Energy Flow by Country",
            xaxis_title="Net Energy Flow (GWh)",
            yaxis_title="",
            height=350,
            margin=dict(l=0, r=20, t=40, b=40),
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="#fafafa"),
            xaxis=dict(gridcolor="#333333", zerolinecolor="#666666"),
            yaxis=dict(gridcolor="#333333"),
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Add import/export legend
        st.markdown("""
        <div style="display: flex; gap: 2rem; justify-content: center; font-size: 0.875rem; color: #808495;">
            <span>← <strong>Export</strong> (negative)</span>
            <span><strong>Import</strong> (positive) →</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        st.markdown("**Interconnector Details**")
        
        # Create detailed table
        detail_df = flow_df[["interconnector", "country", "total_gwh", "avg_mw"]].copy()
        detail_df.columns = ["Link", "Country", "Net (GWh)", "Avg (MW)"]
        detail_df["Net (GWh)"] = detail_df["Net (GWh)"].apply(lambda x: f"{x:+.1f}")
        detail_df["Avg (MW)"] = detail_df["Avg (MW)"].apply(lambda x: f"{x:+.0f}")
        detail_df = detail_df.sort_values("Link")
        
        st.dataframe(detail_df, use_container_width=True, hide_index=True, height=300)


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
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    # Temperature KPIs
    with col1:
        st.markdown("**Temperature**")
        if "temperature" in wdf.columns:
            temp_agg = wdf.groupby("datetime")["temperature"].mean().reset_index()
            avg_temp = temp_agg["temperature"].mean()
            max_temp = temp_agg["temperature"].max()
            min_temp = temp_agg["temperature"].min()
            
            # Calculate trend
            mid = len(temp_agg) // 2
            if mid > 0:
                first_half = temp_agg["temperature"].iloc[:mid].mean()
                second_half = temp_agg["temperature"].iloc[mid:].mean()
                delta = second_half - first_half
                st.metric("Average", f"{avg_temp:.1f}°C", f"{delta:+.1f}°C", help=f"Change from {first_half:.1f}°C → {second_half:.1f}°C")
            else:
                st.metric("Average", f"{avg_temp:.1f}°C")
            
            st.metric("High", f"{max_temp:.1f}°C")
            st.metric("Low", f"{min_temp:.1f}°C")
            
            # Sparkline
            if len(temp_agg) > 1:
                spark = _create_sparkline(temp_agg, "datetime", "temperature", "#ef4444")
                st.altair_chart(spark, use_container_width=True)
        else:
            st.metric("Average", "—")
            st.metric("High", "—")
            st.metric("Low", "—")
    
    # Wind KPIs
    with col2:
        st.markdown("**Wind Speed**")
        if "wind_speed" in wdf.columns:
            wind_agg = wdf.groupby("datetime")["wind_speed"].mean().reset_index()
            avg_wind = wind_agg["wind_speed"].mean()
            peak_wind = wind_agg["wind_speed"].max()
            min_wind = wind_agg["wind_speed"].min()
            
            # Calculate trend
            mid = len(wind_agg) // 2
            if mid > 0:
                first_half = wind_agg["wind_speed"].iloc[:mid].mean()
                second_half = wind_agg["wind_speed"].iloc[mid:].mean()
                delta = ((second_half - first_half) / first_half * 100) if first_half else 0
                st.metric("Average", f"{avg_wind:.1f} m/s", f"{delta:+.1f}%", help=f"Trend: {first_half:.1f} → {second_half:.1f} m/s")
            else:
                st.metric("Average", f"{avg_wind:.1f} m/s")
            
            st.metric("Peak", f"{peak_wind:.1f} m/s")
            st.metric("Minimum", f"{min_wind:.1f} m/s")
            
            # Sparkline
            if len(wind_agg) > 1:
                spark = _create_sparkline(wind_agg, "datetime", "wind_speed", "#3b82f6")
                st.altair_chart(spark, use_container_width=True)
        else:
            st.metric("Average", "—")
            st.metric("Peak", "—")
            st.metric("Minimum", "—")
    
    # Precipitation KPIs
    with col3:
        st.markdown("**Precipitation**")
        if "precipitation" in wdf.columns:
            precip_agg = wdf.groupby("datetime")["precipitation"].sum().reset_index()
            total_precip = precip_agg["precipitation"].sum()
            max_precip = precip_agg["precipitation"].max()
            avg_precip = precip_agg["precipitation"].mean()
            
            st.metric("Total", f"{total_precip:.1f} mm")
            st.metric("Peak Hour", f"{max_precip:.1f} mm")
            st.metric("Avg/Period", f"{avg_precip:.2f} mm")
            
            # Sparkline
            if len(precip_agg) > 1:
                spark = _create_sparkline(precip_agg, "datetime", "precipitation", "#14b8a6")
                st.altair_chart(spark, use_container_width=True)
        else:
            st.metric("Total", "—")
            st.metric("Peak Hour", "—")
            st.metric("Avg/Period", "—")
    
    # Cloud Cover KPIs
    with col4:
        st.markdown("**Cloud Cover**")
        if "cloud_cover" in wdf.columns:
            cloud_agg = wdf.groupby("datetime")["cloud_cover"].mean().reset_index()
            avg_cloud = cloud_agg["cloud_cover"].mean()
            max_cloud = cloud_agg["cloud_cover"].max()
            min_cloud = cloud_agg["cloud_cover"].min()
            
            # Cloud description
            if avg_cloud < 25:
                cloud_desc = "Clear"
            elif avg_cloud < 50:
                cloud_desc = "Partly Cloudy"
            elif avg_cloud < 75:
                cloud_desc = "Mostly Cloudy"
            else:
                cloud_desc = "Overcast"
            
            st.metric("Average", f"{avg_cloud:.0f}%", help=f"Conditions: {cloud_desc}")
            st.metric("Maximum", f"{max_cloud:.0f}%")
            st.metric("Minimum", f"{min_cloud:.0f}%")
            
            # Sparkline
            if len(cloud_agg) > 1:
                spark = _create_sparkline(cloud_agg, "datetime", "cloud_cover", "#94a3b8")
                st.altair_chart(spark, use_container_width=True)
        else:
            st.metric("Average", "—")
            st.metric("Maximum", "—")
            st.metric("Minimum", "—")
    
    st.divider()
    
    # Check if we have more than 7 days of data
    date_range = (wdf["datetime"].max() - wdf["datetime"].min()).days
    
    if date_range >= 7:
        st.subheader("Weather Patterns Heatmap")
        
        # Metric selector
        metric_options = {
            "Temperature (°C)": ("temperature", "°C", [[0.0, "#3b82f6"], [0.5, "#fbbf24"], [1.0, "#ef4444"]]),
            "Wind Speed (m/s)": ("wind_speed", "m/s", [[0.0, "#e0f2fe"], [0.5, "#38bdf8"], [1.0, "#0369a1"]]),
            "Cloud Cover (%)": ("cloud_cover", "%", [[0.0, "#fef3c7"], [0.5, "#9ca3af"], [1.0, "#374151"]]),
            "Precipitation (mm)": ("precipitation", "mm", [[0.0, "#f0fdfa"], [0.5, "#14b8a6"], [1.0, "#0f766e"]]),
        }
        
        selected_metric = st.selectbox(
            "Select weather metric",
            options=list(metric_options.keys()),
            key="weather_heatmap_metric"
        )
        
        col_name, unit, colorscale = metric_options[selected_metric]
        
        if col_name in wdf.columns:
            # Extract hour and weekday
            heatmap_df = wdf.copy()
            heatmap_df["hour"] = heatmap_df["datetime"].dt.hour
            heatmap_df["weekday"] = heatmap_df["datetime"].dt.dayofweek  # 0=Monday
            
            # Group by weekday and hour, calculate mean
            heatmap_data = heatmap_df.groupby(["weekday", "hour"])[col_name].mean().reset_index()
            heatmap_data.columns = ["weekday", "hour", "value"]
            
            # Pivot to 7x24 matrix
            pivot_df = heatmap_data.pivot(index="weekday", columns="hour", values="value")
            pivot_df = pivot_df.reindex(index=range(7), columns=range(24))
            
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            # Prepare hover text
            hover_text = []
            for weekday_idx in range(7):
                row_text = []
                for hour in range(24):
                    val = pivot_df.loc[weekday_idx, hour] if pd.notna(pivot_df.loc[weekday_idx, hour]) else 0
                    row_text.append(
                        f"<b>{day_names[weekday_idx]}</b><br>"
                        f"Hour: {hour:02d}:00<br>"
                        f"{selected_metric.split(' ')[0]}: {val:.1f} {unit}"
                    )
                hover_text.append(row_text)
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=[f"{h:02d}:00" for h in range(24)],
                y=day_names,
                colorscale=colorscale,
                hoverinfo="text",
                text=hover_text,
                colorbar=dict(
                    title=dict(text=unit, side="right"),
                    len=0.9,
                ),
            ))
            
            fig.update_layout(
                title=dict(
                    text=f"{selected_metric} by Hour & Day of Week",
                    x=0.5,
                    font=dict(size=16)
                ),
                xaxis=dict(
                    title="Hour of Day",
                    tickmode="array",
                    tickvals=[f"{h:02d}:00" for h in range(0, 24, 3)],
                    ticktext=["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
                    side="bottom",
                    gridcolor="#333333",
                ),
                yaxis=dict(
                    title="Day of Week",
                    autorange="reversed",
                    gridcolor="#333333",
                ),
                height=400,
                margin=dict(l=100, r=20, t=50, b=60),
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117",
                font=dict(color="#fafafa"),
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # Show peak/low summary
            if not heatmap_data.empty:
                peak_row = heatmap_data.loc[heatmap_data["value"].idxmax()]
                low_row = heatmap_data.loc[heatmap_data["value"].idxmin()]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div style="background: #1a1a2e; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #ef4444;">
                        <strong style="color: #fafafa;">Peak</strong><br>
                        <span style="color: #e0e0e0;">{day_names[int(peak_row['weekday'])]} at {int(peak_row['hour']):02d}:00 — {peak_row['value']:.1f} {unit}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div style="background: #1a1a2e; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #22c55e;">
                        <strong style="color: #fafafa;">Lowest</strong><br>
                        <span style="color: #e0e0e0;">{day_names[int(low_row['weekday'])]} at {int(low_row['hour']):02d}:00 — {low_row['value']:.1f} {unit}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning(f"No {col_name} data available.")
    else:
        st.info("Weather heatmap requires more than 7 days of data. Please expand your date range to see patterns by hour and day of week.")


def generation_mix_stacked_bar(carbon_df: pd.DataFrame):
    """Plot a stacked bar chart of renewable vs non-renewable generation mix."""
    if carbon_df.empty:
        st.info("No carbon data available for the selected date range.")
        return

    # Define groupings and colors
    group_map = {
        "Fossil Fuels": [
            ("gen_coal", "Coal", "#636363"),
            ("gen_gas_imports", "Gas", "#fc8d62")  # Merged Gas + Imports
        ],
        "Renewables": [
            ("gen_biomass", "Biomass", "#8dd3c7"),
            ("gen_hydro", "Hydro", "#1f78b4"),
            ("gen_solar", "Solar", "#ffd92f"),
            ("gen_wind", "Wind", "#66c2a5")
        ],
        "Low Carbon": [
            ("gen_nuclear", "Nuclear", "#bebada"),
            ("gen_other", "Other Low Carbon", "#b3b3b3")  # fallback
        ],
        "Other": [
            ("gen_other", "Other", "#fb8072")
        ]
    }

    # Find available columns and calculate means
    mix_df = carbon_df.copy()
    group_cols = ["datetime"] if "datetime" in mix_df.columns else []
    # Special handling: merge gen_gas and gen_imports into gen_gas_imports
    temp_df = mix_df.copy()
    if "gen_gas" in temp_df.columns or "gen_imports" in temp_df.columns:
        temp_df["gen_gas_imports"] = temp_df.get("gen_gas", 0) + temp_df.get("gen_imports", 0)
    all_cols = [col for group in group_map.values() for col, _, _ in group]
    available_cols = [col for col in all_cols if col in temp_df.columns]
    if not available_cols:
        st.warning("No generation mix columns found in data.")
        return
    if group_cols:
        temp_df = temp_df.groupby(group_cols)[available_cols].mean().reset_index()
    else:
        temp_df = temp_df[available_cols].mean().to_frame().T

    avg_vals = temp_df[available_cols].mean().to_dict()
    total_percent = sum(avg_vals.values())
    total_gw = temp_df["total_generation_gw"].mean() if "total_generation_gw" in temp_df.columns else None

    bar_data = []
    for group, sources in group_map.items():
        for col, name, color in sources:
            if col in avg_vals:
                percent = avg_vals[col]
                gw = (percent / 100 * total_gw) if total_gw else None
                bar_data.append({
                    "Group": group,
                    "Source": name,
                    "Percent": percent,
                    "GW": gw,
                    "Color": color
                })

    plot_df = pd.DataFrame(bar_data)
    plot_df = plot_df[plot_df["Percent"] > 0]

    # Plot grouped stacked bars
    fig = go.Figure()
    for group in plot_df["Group"].unique():
        group_df = plot_df[plot_df["Group"] == group]
        fig.add_trace(go.Bar(
            x=[group]*len(group_df),
            y=group_df["Percent"],
            name=group,
            marker_color=group_df["Color"],
            width=0.3,  # Make bars thinner
            text=[
                (f"{row['Percent']:.1f}%" + (f"<br>{row['GW']:.1f} GW" if row['GW'] is not None else ""))
                for _, row in group_df.iterrows()
            ],
            textposition="inside",
            customdata=group_df["Source"],
            hovertemplate="%{customdata}: %{y:.1f}%" + ("<br>%{text}" if total_gw else "") + "<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        title="Generation Type - Today",
        yaxis=dict(title="Generation (% of total)", range=[0, 100], color="#fafafa"),
        xaxis=dict(title="", color="#fafafa"),
        plot_bgcolor="#232734",
        paper_bgcolor="#232734",
        font=dict(color="#fafafa"),
        showlegend=False,
        height=450,
        width=900,  # Wider figure for thinner look
        margin=dict(t=60, b=40, l=40, r=20)
    )
    st.plotly_chart(fig, use_container_width=True)

def exploratory_scatter_plot(weather_df: pd.DataFrame, demand_df: pd.DataFrame, carbon_df: pd.DataFrame):
    """Scatter plot with dropdowns: X=weather variable, Y=energy variable (demand/carbon/renewable proxy), using filtered timestamps."""
    # Merge on datetime
    if weather_df.empty or (demand_df.empty and carbon_df.empty):
        st.info("Not enough data for scatter plot.")
        return

    # Prepare mergeable dataframes
    wdf = weather_df.copy()
    ddf = demand_df.copy()
    cdf = carbon_df.copy()
    # Convert all to pandas datetime (remove tz info for merge)
    for df in [wdf, ddf, cdf]:
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize(None)

    # Merge all on datetime (inner join)
    merged = wdf
    if not ddf.empty:
        merged = pd.merge(merged, ddf, on="datetime", how="inner", suffixes=("", "_d"))
    if not cdf.empty:
        merged = pd.merge(merged, cdf, on="datetime", how="inner", suffixes=("", "_c"))

    # Weather variables for X
    weather_vars = [col for col in ["temperature", "wind_speed", "cloud_cover", "humidity", "precipitation"] if col in merged.columns]
    # Energy variables for Y
    energy_vars = []
    if "tsd" in merged.columns:
        energy_vars.append(("tsd", "Demand (MW)"))
    if "forecast" in merged.columns:
        energy_vars.append(("forecast", "Carbon Intensity (gCO₂/kWh)"))
    # Renewable proxy: wind + solar generation if available
    if "gen_wind" in merged.columns or "gen_solar" in merged.columns:
        merged["renewable_proxy"] = merged.get("gen_wind", 0) + merged.get("gen_solar", 0)
        energy_vars.append(("renewable_proxy", "Renewable Proxy (%)"))

    if not weather_vars or not energy_vars:
        st.info("No suitable variables for scatter plot.")
        return

    x_var = st.selectbox("Weather variable (X)", weather_vars, key="scatter_x")
    y_var, y_label = st.selectbox("Energy variable (Y)", energy_vars, format_func=lambda x: x[1], key="scatter_y")

    fig = px.scatter(
        merged, x=x_var, y=y_var,
        title=f"Scatter: {x_var} vs {y_label}",
        labels={x_var: x_var.replace('_', ' ').title(), y_var: y_label},
        opacity=0.7,
        color_discrete_sequence=["#38bdf8"],
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
def render_weather_energy_relevance(weather_df: pd.DataFrame):
    """Panel showing wind and solar availability indices with Low/Moderate/High labels."""
    if weather_df.empty:
        st.info("No weather data available for the selected date range.")
        return

    # Wind index: use average wind speed
    wind_speed = weather_df["wind_speed"].mean() if "wind_speed" in weather_df.columns else None
    # Solar index: use average (100 - cloud_cover)
    solar_index = None
    if "cloud_cover" in weather_df.columns:
        solar_index = 100 - weather_df["cloud_cover"].mean()

    def label_index(val, low, high):
        if val is None:
            return ("N/A", "#888888")
        if val < low:
            return ("Low", "#ef4444")
        elif val < high:
            return ("Moderate", "#eab308")
        else:
            return ("High", "#22c55e")

    wind_label, wind_color = label_index(wind_speed, 10, 20)
    solar_label, solar_color = label_index(solar_index, 30, 60)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #232742 0%, #1a1a2e 100%); padding: 1rem 1.2rem; border-radius: 10px; border-left: 3px solid #22c55e; margin: 1rem 0;">
        <h4 style="margin: 0 0 0.7rem 0; color: #fff; font-size: 1.05rem; font-weight: 700; letter-spacing: 0.01em;">Weather → Energy Relevance</h4>
        <div style="display: flex; gap: 2.2rem; align-items: flex-end;">
            <div>
                <span style="color: #7ee787; font-weight: 700; font-size: 1rem;">Wind Availability</span><br>
                <span style="font-size: 2rem; color: {wind_color}; font-weight: 800; letter-spacing: 0.01em;">{wind_label}</span>
                <span style="color: #e0e0e0; font-size: 1rem; font-weight: 400;"> ({wind_speed:.1f} km/h)</span>
            </div>
            <div>
                <span style="color: #ffe066; font-weight: 700; font-size: 1rem;">Solar Availability</span><br>
                <span style="font-size: 2rem; color: {solar_color}; font-weight: 800; letter-spacing: 0.01em;">{solar_label}</span>
                <span style="color: #e0e0e0; font-size: 1rem; font-weight: 400;"> ({solar_index:.1f}%)</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)