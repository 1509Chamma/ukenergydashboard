import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from statsmodels.tsa.seasonal import seasonal_decompose
import altair as alt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

TIMEOUT_SECONDS = 30 * 60  # 30 minutes

def create_interactive_forecast_chart(combined_df, target_col, y_test, y_pred, model, X_test, feature_cols):
    """Create interactive Plotly chart with predictions and forecast for next week"""
    
    # Prepare test data with actual vs predicted
    test_indices = combined_df.tail(len(y_test)).index
    test_dates = combined_df.loc[test_indices, 'datetime'].values
    
    # Create forecast for next 7 days
    last_datetime = combined_df['datetime'].max()
    forecast_dates = pd.date_range(start=last_datetime + pd.Timedelta(hours=1), periods=7*24, freq='1H')
    
    # Use last values and patterns for simple forecast
    last_X = X_test.iloc[-1:].values
    forecast_values = []
    X_current = last_X.copy()
    
    for _ in range(len(forecast_dates)):
        next_pred = model.predict(X_current.reshape(1, -1))[0]
        forecast_values.append(next_pred)
        X_current = np.roll(X_current, -1)
        X_current[-1] = next_pred
    
    # Filter to last 2 weeks for forecast view
    two_weeks_ago = last_datetime - pd.Timedelta(days=14)
    recent_mask = test_dates >= np.datetime64(two_weeks_ago)
    recent_test_dates = test_dates[recent_mask]
    recent_y_test = y_test.values[recent_mask]
    recent_y_pred = y_pred[recent_mask]
    
    # Get last 180 days for overview
    days_180_ago = last_datetime - pd.Timedelta(days=180)
    last_180_mask = combined_df['datetime'] >= days_180_ago
    last_180_df = combined_df[last_180_mask]
    
    # Create subplots: top = zoomed forecast (2 weeks + 7 day forecast), bottom = 180 day overview
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Forecast View (Last 2 Weeks + 7-Day Forecast)', 'Last 180 Days Overview'),
        vertical_spacing=0.12,
        row_heights=[0.5, 0.5]
    )
    
    # TOP CHART: Zoomed into last 2 weeks predictions and forecast
    # Actual values from test set (last 2 weeks)
    fig.add_trace(
        go.Scatter(
            x=recent_test_dates, 
            y=recent_y_test,
            mode='lines',
            name='Actual',
            line=dict(color='blue', width=2),
            hovertemplate='%{x}<br>Actual: %{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Predicted values (dotted line, last 2 weeks)
    fig.add_trace(
        go.Scatter(
            x=recent_test_dates,
            y=recent_y_pred,
            mode='lines',
            name='Predicted',
            line=dict(color='orange', width=2, dash='dot'),
            hovertemplate='%{x}<br>Predicted: %{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Forecast (dashed line)
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_values,
            mode='lines',
            name='Forecast (7 days)',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate='%{x}<br>Forecast: %{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # BOTTOM CHART: Last 180 days overview with actual target values
    fig.add_trace(
        go.Scatter(
            x=last_180_df['datetime'],
            y=last_180_df[target_col],
            mode='lines',
            name='Historical (180 days)',
            line=dict(color='green', width=1.5),
            hovertemplate='%{x}<br>Value: %{y:.2f}<extra></extra>',
            showlegend=True
        ),
        row=2, col=1
    )
    
    # Update layout for interactivity
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text=target_col, row=1, col=1)
    fig.update_yaxes(title_text=target_col, row=2, col=1)
    
    fig.update_layout(
        height=700,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def prepare_time_series_features(df, target_col, feature_cols, datetime_col='datetime'):
    """Prepare features with lagged values and time components"""
    if df.empty or target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")
    
    df = df.copy()
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.sort_values(datetime_col)
    
    # Keep only numeric columns for features
    numeric_features = [f for f in feature_cols if df[f].dtype in [np.float64, np.int64, float, int]]
    if not numeric_features:
        raise ValueError("No numeric features found. Please select numeric columns.")
    
    # Add time-based features
    df['hour'] = df[datetime_col].dt.hour
    df['day_of_week'] = df[datetime_col].dt.dayofweek
    df['day_of_month'] = df[datetime_col].dt.day
    df['month'] = df[datetime_col].dt.month
    
    # Add lagged features for target
    for lag in [1, 24, 168]:  # 1 hour, 1 day, 1 week
        df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
    
    # Drop rows with NaN from lagging
    df = df.dropna()
    
    if df.empty:
        raise ValueError("No complete rows after adding lag features. Need more data.")
    
    # Build feature list
    all_features = numeric_features + ['hour', 'day_of_week', 'day_of_month', 'month']
    all_features += [f'{target_col}_lag_{lag}' for lag in [1, 24, 168]]
    all_features = [f for f in all_features if f in df.columns and f != target_col]
    
    if not all_features:
        raise ValueError("No valid features after filtering. Check input data.")
    
    X = df[all_features]
    y = df[target_col]
    
    return train_test_split(X, y, test_size=0.2, shuffle=False, random_state=42)

def run_linear_regression(X_train, X_test, y_train, y_test, progress_bar, status_text):
    """Train Linear Regression and return metrics"""
    status_text.text("Training Linear Regression...")
    progress_bar.progress(0.1)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    progress_bar.progress(0.5)
    
    y_pred = model.predict(X_test)
    progress_bar.progress(0.9)
    
    metrics = {
        'MAE': mean_absolute_error(y_test, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
        'R²': r2_score(y_test, y_pred)
    }
    
    progress_bar.progress(1.0)
    status_text.text("Linear Regression complete!")
    
    return metrics, y_pred, model

def run_random_forest(X_train, X_test, y_train, y_test, progress_bar, status_text):
    """Train Random Forest and return metrics"""
    status_text.text("Training Random Forest...")
    progress_bar.progress(0.1)
    
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    progress_bar.progress(0.6)
    
    y_pred = model.predict(X_test)
    progress_bar.progress(0.9)
    
    metrics = {
        'MAE': mean_absolute_error(y_test, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
        'R²': r2_score(y_test, y_pred)
    }
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False).head(10)
    
    progress_bar.progress(1.0)
    status_text.text("Random Forest complete!")
    
    return metrics, y_pred, model, feature_importance

def run_correlation_analysis(df, target_col, feature_cols):
    """Compute correlation matrix"""
    numeric_cols = [target_col] + [f for f in feature_cols if f in df.columns]
    corr_matrix = df[numeric_cols].corr()
    
    # Get correlations with target
    target_corr = corr_matrix[target_col].drop(target_col).sort_values(ascending=False)
    
    return corr_matrix, target_corr

def render_time_series_experimentation(supabase, min_date, max_date):
    """Render the time series experimentation UI with lazy data loading"""
    st.markdown("### Time Series Experimentation")
    
    # Initialize session state for experiment data
    if 'experiment_data_loaded' not in st.session_state:
        st.session_state.experiment_data_loaded = False
        st.session_state.experiment_demand_df = pd.DataFrame()
        st.session_state.experiment_carbon_df = pd.DataFrame()
        st.session_state.experiment_weather_df = pd.DataFrame()
        st.session_state.selected_exp_region = None
    
    # Region selector and load button
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Fetch available regions
        try:
            regions_query = supabase.table("carbon_intensity").select("region_name").execute()
            available_regions = sorted(set([r.get("region_name") for r in regions_query.data if r.get("region_name")]))
        except:
            available_regions = []
        
        selected_region = st.selectbox(
            "Select Region", 
            available_regions,
            key="exp_region_select",
            help="Select a region to load data for experimentation"
        )
    
    # Load data only when button is clicked
    with col2:
        if st.button("Load Data", key="load_exp_data", use_container_width=True, type="primary"):
            if not selected_region:
                st.error("Please select a region first")
            else:
                from data.loaders import fetch_demand_range, fetch_carbon_range, fetch_weather_range
                
                with st.spinner(f"Loading data for {selected_region}..."):
                    # Fetch demand data (no region filter)
                    st.session_state.experiment_demand_df = fetch_demand_range(supabase, min_date, max_date)
                    
                    # Fetch carbon and weather for selected region only
                    st.session_state.experiment_carbon_df = fetch_carbon_range(supabase, min_date, max_date, (selected_region,))
                    st.session_state.experiment_weather_df = fetch_weather_range(supabase, min_date, max_date, (selected_region,))
                    st.session_state.selected_exp_region = selected_region
                    st.session_state.experiment_data_loaded = True
                
                st.success(f"Data loaded for {selected_region}")
    
    if not st.session_state.experiment_data_loaded:
        st.info("Select a region and click **Load Data** to begin experimentation.")
        return
    
    st.divider()
    
    # Use cached data
    demand_df = st.session_state.experiment_demand_df
    carbon_df = st.session_state.experiment_carbon_df
    weather_df = st.session_state.experiment_weather_df
    
    # Helper function to standardize datetime column to timezone-naive UTC
    def standardize_datetime(df, datetime_col='datetime'):
        """Ensure datetime is timezone-naive and in UTC"""
        if df.empty:
            return df
        
        if datetime_col not in df.columns:
            timestamp_cols = df.select_dtypes(include=['datetime64']).columns
            if len(timestamp_cols) > 0:
                df = df.rename(columns={timestamp_cols[0]: datetime_col})
        
        if datetime_col in df.columns:
            # Convert to datetime
            df[datetime_col] = pd.to_datetime(df[datetime_col])
            # Remove timezone info to make timezone-naive
            if df[datetime_col].dt.tz is not None:
                df[datetime_col] = df[datetime_col].dt.tz_localize(None)
        
        return df
    
    # Combine datasets - start with demand as base
    combined_df = demand_df.copy() if not demand_df.empty else pd.DataFrame()
    combined_df = standardize_datetime(combined_df, 'datetime')
    
    # Merge carbon data using outer join to preserve all demand data
    if not carbon_df.empty:
        carbon_df = standardize_datetime(carbon_df, 'datetime')
        numeric_carbon_cols = carbon_df.select_dtypes(include=[np.number]).columns.tolist()
        agg_dict = {col: 'mean' for col in numeric_carbon_cols}
        
        carbon_agg = carbon_df.groupby('datetime').agg(agg_dict).reset_index()
        carbon_agg.columns = ['datetime'] + [f'carbon_{c}' for c in carbon_agg.columns[1:]]
        
        if not combined_df.empty and 'datetime' in combined_df.columns:
            combined_df = pd.merge(combined_df, carbon_agg, on='datetime', how='outer')
        elif combined_df.empty:
            combined_df = carbon_agg
    
    # Merge weather data using outer join
    if not weather_df.empty:
        weather_df = standardize_datetime(weather_df, 'datetime')
        numeric_weather_cols = weather_df.select_dtypes(include=[np.number]).columns.tolist()
        agg_dict = {col: 'mean' for col in numeric_weather_cols}
        
        weather_agg = weather_df.groupby('datetime').agg(agg_dict).reset_index()
        weather_agg.columns = ['datetime'] + [f'weather_{c}' for c in weather_agg.columns[1:]]
        
        if not combined_df.empty and 'datetime' in combined_df.columns:
            combined_df = pd.merge(combined_df, weather_agg, on='datetime', how='outer')
        elif combined_df.empty:
            combined_df = weather_agg
    
    if combined_df.empty:
        st.warning("No data available for experimentation. Please load data first.")
        return
    
    # Ensure datetime is standardized after all merges
    combined_df = standardize_datetime(combined_df, 'datetime')
    
    # Sort by datetime and drop duplicates
    combined_df = combined_df.sort_values('datetime').drop_duplicates(subset=['datetime'])
    
    # Fill missing values for numeric columns with forward fill then backward fill
    numeric_cols_all = combined_df.select_dtypes(include=[np.number]).columns.tolist()
    combined_df[numeric_cols_all] = combined_df[numeric_cols_all].fillna(method='ffill').fillna(method='bfill').fillna(0)
    
    # Get only numeric columns for modeling
    numeric_cols = combined_df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude datetime and all ID columns
    exclude_cols = ['datetime', 'id', 'carbon_id', 'carbon_region_id', 'weather_id', 'weather_region_id', 'region_id']
    numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    if not numeric_cols:
        st.error("No numeric columns found in the combined data.")
        return
    
    # Feature explanations
    with st.expander("📊 Feature Descriptions"):
        st.markdown("**Available features for modeling:**")
        
        feature_descriptions = {
            # Demand features from NESO API
            'nd': 'National Demand - Estimated total GB electricity demand including embedded generation (MW)',
            'tsd': 'Transmission System Demand - Demand seen by the transmission network, excludes embedded generation (MW)',
            'england_wales_demand': 'Electricity demand specific to England and Wales (MW)',
            'embedded_wind_generation': 'Electricity generated by wind connected to distribution networks, not transmission (MW)',
            'embedded_wind_capacity': 'Installed capacity of embedded wind generation (MW)',
            'embedded_solar_generation': 'Electricity generated by embedded solar PV (MW)',
            'embedded_solar_capacity': 'Installed capacity of embedded solar PV (MW)',
            'non_bm_stor': 'Non-Balancing Mechanism storage output, e.g. small-scale batteries (MW)',
            'pump_storage_pumping': 'Electricity demand used to pump water into pumped-storage hydro, negative net generation (MW)',
            'scottish_transfer': 'Net electricity transfer between Scotland and England/Wales (MW)',
            'ifa_flow': 'Power flow on the IFA interconnector (GB-France) (MW)',
            'ifa2_flow': 'Power flow on the IFA2 interconnector (GB-France) (MW)',
            'britned_flow': 'Power flow on the BritNed interconnector (GB-Netherlands) (MW)',
            'moyle_flow': 'Power flow on the Moyle interconnector (GB-Northern Ireland) (MW)',
            'east_west_flow': 'Power flow on the East-West interconnector (GB-Ireland) (MW)',
            'nemo_flow': 'Power flow on the NEMO interconnector (GB-Belgium) (MW)',
            'nsl_flow': 'Power flow on the North Sea Link interconnector (GB-Norway) (MW)',
            'eleclink_flow': 'Power flow on the ElecLink interconnector (GB-France) (MW)',
            'viking_flow': 'Power flow on the Viking Link interconnector (GB-Denmark) (MW)',
            'greenlink_flow': 'Power flow on the Greenlink interconnector (GB-Ireland) (MW)',
            
            # Carbon intensity features from UK Carbon Intensity API
            'carbon_forecast': 'Forecasted carbon intensity for this region (gCO2/kWh)',
            'carbon_gen_biomass': 'Percentage of electricity generation from biomass (%)',
            'carbon_gen_coal': 'Percentage of electricity generation from coal (%)',
            'carbon_gen_imports': 'Percentage of electricity generation from imports (%)',
            'carbon_gen_gas': 'Percentage of electricity generation from gas (%)',
            'carbon_gen_nuclear': 'Percentage of electricity generation from nuclear (%)',
            'carbon_gen_other': 'Percentage of electricity generation from other sources (%)',
            'carbon_gen_hydro': 'Percentage of electricity generation from hydro (%)',
            'carbon_gen_solar': 'Percentage of electricity generation from solar (%)',
            'carbon_gen_wind': 'Percentage of electricity generation from wind (%)',
            
            # Weather features from Open-Meteo API
            'weather_temperature': 'Air temperature at 2m height (°C)',
            'weather_humidity': 'Relative humidity at 2m height (%)',
            'weather_wind_speed': 'Wind speed at 10m height (km/h)',
            'weather_cloud_cover': 'Total cloud cover (%)',
            'weather_precipitation': 'Total precipitation - rain, showers, snow (mm)',
        }
        
        feature_table_data = []
        for col in numeric_cols:
            description = feature_descriptions.get(col, 'Feature from loaded dataset')
            feature_table_data.append({"Feature": col, "Description": description})
        
        if feature_table_data:
            st.dataframe(
                pd.DataFrame(feature_table_data),
                use_container_width=True,
                hide_index=True
            )
    
    # Feature and target selection
    col1, col2 = st.columns(2)
    
    with col1:
        target_feature = st.selectbox("Target Feature", numeric_cols, key="exp_target")
    
    # Get available input features (exclude target)
    available_inputs = [f for f in numeric_cols if f != target_feature]
    
    with col2:
        input_features = st.multiselect(
            "Input Features", 
            available_inputs,
            default=available_inputs[:min(5, len(available_inputs))],
            key="exp_inputs"
        )
        # Filter out target from input features if it somehow got selected
        input_features = [f for f in input_features if f != target_feature]
    
    # Method selection
    method = st.selectbox(
        "Methodology",
        ["Linear Regression", "Random Forest", "Correlation Analysis"],
        key="exp_method"
    )
    
    # Run button
    if st.button("Run Experiment", key="run_exp"):
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            if method in ["Linear Regression", "Random Forest"]:
                if not input_features:
                    st.error("Please select at least one input feature.")
                    return
                
                status_text.text("Preparing features...")
                try:
                    X_train, X_test, y_train, y_test = prepare_time_series_features(
                        combined_df, target_feature, input_features
                    )
                except ValueError as ve:
                    st.error(f"Feature preparation error: {str(ve)}")
                    return
                
                progress_bar.progress(0.05)
                
                if method == "Linear Regression":
                    metrics, y_pred, model = run_linear_regression(
                        X_train, X_test, y_train, y_test, progress_bar, status_text
                    )
                    
                    # Display metrics
                    st.success(f"Training complete in {time.time() - start_time:.2f}s")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("MAE", f"{metrics['MAE']:.2f}")
                    col2.metric("RMSE", f"{metrics['RMSE']:.2f}")
                    col3.metric("R²", f"{metrics['R²']:.3f}")
                    
                    st.markdown("**Interactive Predictions & Forecast**")
                    # Create interactive chart with forecast
                    fig = create_interactive_forecast_chart(combined_df, target_feature, y_test, y_pred, model, X_test, input_features)
                    st.plotly_chart(fig, use_container_width=True)
                
                elif method == "Random Forest":
                    metrics, y_pred, model, feature_importance = run_random_forest(
                        X_train, X_test, y_train, y_test, progress_bar, status_text
                    )
                    
                    st.success(f"Training complete in {time.time() - start_time:.2f}s")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("MAE", f"{metrics['MAE']:.2f}")
                    col2.metric("RMSE", f"{metrics['RMSE']:.2f}")
                    col3.metric("R²", f"{metrics['R²']:.3f}")
                    
                    # Feature importance
                    st.markdown("**Top 10 Important Features**")
                    st.dataframe(feature_importance, use_container_width=True)
                    
                    st.markdown("**Interactive Predictions & Forecast**")
                    # Create interactive chart with forecast
                    fig = create_interactive_forecast_chart(combined_df, target_feature, y_test, y_pred, model, X_test, input_features)
                    st.plotly_chart(fig, use_container_width=True)
            
            elif method == "Correlation Analysis":
                progress_bar.progress(0.5)
                status_text.text("Computing correlations...")
                
                corr_matrix, target_corr = run_correlation_analysis(
                    combined_df, target_feature, input_features
                )
                
                progress_bar.progress(1.0)
                status_text.text("Correlation analysis complete!")
                
                st.success(f"Analysis complete in {time.time() - start_time:.2f}s")
                
                st.markdown(f"**Correlations with {target_feature}**")
                
                # Sort by correlation strength
                corr_df = pd.DataFrame({'Feature': target_corr.index, 'Correlation': target_corr.values})
                corr_df = corr_df.sort_values('Correlation', key=abs, ascending=False)
                
                # Create horizontal bar chart with color coding
                fig = go.Figure()
                
                colors = ['red' if x < -0.5 else 'orange' if x < 0 else 'lightgreen' if x < 0.5 else 'green' 
                         for x in corr_df['Correlation']]
                
                fig.add_trace(go.Bar(
                    y=corr_df['Feature'],
                    x=corr_df['Correlation'],
                    orientation='h',
                    marker=dict(
                        color=corr_df['Correlation'],
                        colorscale='RdBu',
                        cmin=-1,
                        cmax=1,
                        colorbar=dict(title="Correlation")
                    ),
                    text=[f"{val:.3f}" for val in corr_df['Correlation']],
                    textposition='outside',
                    hovertemplate='%{y}: %{x:.3f}<extra></extra>'
                ))
                
                fig.update_layout(
                    title=f"Feature Correlations with {target_feature}",
                    xaxis_title="Correlation Coefficient",
                    yaxis_title="Features",
                    height=400,
                    margin=dict(l=150, r=50, t=50, b=50)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Heatmap of full correlation matrix
                st.markdown("**Full Correlation Matrix**")
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmid=0,
                    zmin=-1,
                    zmax=1,
                    hovertemplate='%{y} vs %{x}: %{z:.3f}<extra></extra>',
                    colorbar=dict(title="Correlation")
                ))
                
                fig_heatmap.update_layout(height=600, width=700)
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Statistical summary
                st.markdown("**Correlation Insights**")
                col1, col2, col3 = st.columns(3)
                
                strongest_corr = corr_df.iloc[0]
                col1.metric(
                    "Strongest Correlation",
                    strongest_corr['Feature'],
                    f"{strongest_corr['Correlation']:.3f}"
                )
                
                positive_corrs = (corr_df['Correlation'] > 0.3).sum()
                col2.metric("Positive Correlations (>0.3)", positive_corrs)
                
                negative_corrs = (corr_df['Correlation'] < -0.3).sum()
                col3.metric("Negative Correlations (<-0.3)", negative_corrs)
            
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > TIMEOUT_SECONDS:
                st.warning(f"Training exceeded 30-minute limit ({elapsed/60:.1f} min)")
        
        except Exception as e:
            status_text.text("")
            progress_bar.empty()
            st.error(f"Error during experimentation: {str(e)}")
