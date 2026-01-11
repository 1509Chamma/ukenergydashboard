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

TIMEOUT_SECONDS = 30 * 60  # 30 minutes

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

def run_seasonal_decomposition(df, target_col, datetime_col='datetime', period=24):
    """Perform seasonal decomposition"""
    df = df.copy()
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.sort_values(datetime_col).set_index(datetime_col)
    
    if len(df) < 2 * period:
        return None
    
    decomposition = seasonal_decompose(df[target_col], model='additive', period=period)
    
    return decomposition

def render_time_series_experimentation(supabase, min_date, max_date):
    """Render the time series experimentation UI with lazy data loading"""
    st.markdown("### Time Series Experimentation")
    
    # Initialize session state for experiment data
    if 'experiment_data_loaded' not in st.session_state:
        st.session_state.experiment_data_loaded = False
        st.session_state.experiment_demand_df = pd.DataFrame()
        st.session_state.experiment_carbon_df = pd.DataFrame()
        st.session_state.experiment_weather_df = pd.DataFrame()
    
    col1, col2 = st.columns([2, 8])
    
    # Load data only when button is clicked
    with col1:
        if st.button("📊 Load Data", key="load_exp_data", use_container_width=True):
            from data.loaders import fetch_demand_range, fetch_carbon_range, fetch_weather_range
            from datetime import datetime as dt
            
            with st.spinner("Loading data..."):
                # Fetch demand data
                st.session_state.experiment_demand_df = fetch_demand_range(supabase, min_date, max_date)
                
                # Query all unique regions from carbon_intensity table
                try:
                    regions_query = supabase.table("carbon_intensity").select("region_name").execute()
                    all_regions = tuple(set([r.get("region_name") for r in regions_query.data if r.get("region_name")]))
                    if not all_regions:
                        all_regions = ()
                except Exception as e:
                    st.error(f"Could not fetch regions: {str(e)}")
                    all_regions = ()
                
                # Fetch carbon and weather for all available regions
                if all_regions:
                    st.session_state.experiment_carbon_df = fetch_carbon_range(supabase, min_date, max_date, all_regions)
                    st.session_state.experiment_weather_df = fetch_weather_range(supabase, min_date, max_date, all_regions)
                else:
                    st.session_state.experiment_carbon_df = pd.DataFrame()
                    st.session_state.experiment_weather_df = pd.DataFrame()
                
                st.session_state.experiment_data_loaded = True
    
    with col2:
        if st.session_state.experiment_data_loaded:
            demand_count = len(st.session_state.experiment_demand_df)
            carbon_count = len(st.session_state.experiment_carbon_df)
            weather_count = len(st.session_state.experiment_weather_df)
            st.markdown(f"✓ **Data loaded:** {demand_count} demand | {carbon_count} carbon | {weather_count} weather records")
        else:
            st.markdown("Click **Load Data** to start")
    
    if not st.session_state.experiment_data_loaded:
        return
    
    # Use cached data
    demand_df = st.session_state.experiment_demand_df
    carbon_df = st.session_state.experiment_carbon_df
    weather_df = st.session_state.experiment_weather_df
    
    st.divider()
    
    # Combine datasets
    combined_df = demand_df.copy() if not demand_df.empty else pd.DataFrame()
    
    # Rename datetime column if it exists and is named differently
    if not combined_df.empty and 'datetime' not in combined_df.columns:
        # Try to find a timestamp column
        timestamp_cols = combined_df.select_dtypes(include=['datetime64']).columns
        if len(timestamp_cols) > 0:
            combined_df = combined_df.rename(columns={timestamp_cols[0]: 'datetime'})
    
    if not carbon_df.empty:
        # Aggregate carbon by datetime (average only numeric columns)
        numeric_carbon_cols = carbon_df.select_dtypes(include=[np.number]).columns.tolist()
        agg_dict = {col: 'mean' for col in numeric_carbon_cols}
        
        carbon_agg = carbon_df.groupby('datetime').agg(agg_dict).reset_index()
        carbon_agg.columns = ['datetime'] + [f'carbon_{c}' for c in carbon_agg.columns[1:]]
        
        if not combined_df.empty and 'datetime' in combined_df.columns:
            combined_df = pd.merge(combined_df, carbon_agg, on='datetime', how='inner')
        elif combined_df.empty:
            combined_df = carbon_agg
    
    if not weather_df.empty:
        # Aggregate weather by datetime (average only numeric columns)
        numeric_weather_cols = weather_df.select_dtypes(include=[np.number]).columns.tolist()
        agg_dict = {col: 'mean' for col in numeric_weather_cols}
        
        weather_agg = weather_df.groupby('datetime').agg(agg_dict).reset_index()
        weather_agg.columns = ['datetime'] + [f'weather_{c}' for c in weather_agg.columns[1:]]
        
        if not combined_df.empty and 'datetime' in combined_df.columns:
            combined_df = pd.merge(combined_df, weather_agg, on='datetime', how='inner')
        elif combined_df.empty:
            combined_df = weather_agg
    
    if combined_df.empty:
        st.warning("No data available for experimentation. Please select a date range with data.")
        return
    
    combined_df = combined_df.dropna()
    
    # Get only numeric columns
    numeric_cols = combined_df.select_dtypes(include=[np.number]).columns.tolist()
    if 'datetime' in numeric_cols:
        numeric_cols.remove('datetime')
    
    if not numeric_cols:
        st.error("No numeric columns found in the combined data.")
        st.write("Debug - Available columns:", combined_df.columns.tolist())
        return
    
    # Debug info (expandable)
    with st.expander("Debug Info"):
        st.write(f"Combined data shape: {combined_df.shape}")
        st.write(f"Available numeric columns: {numeric_cols}")
        st.write(f"Sample of combined data:")
        st.dataframe(combined_df.head())
    
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
        ["Linear Regression", "Random Forest", "Correlation Analysis", "Seasonal Decomposition"],
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
                    
                    # Plot predictions vs actual
                    results_df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
                    chart = alt.Chart(results_df.reset_index()).mark_line().encode(
                        x='index:Q',
                        y=alt.Y('value:Q', title=target_feature),
                        color='variable:N'
                    ).transform_fold(['Actual', 'Predicted'], as_=['variable', 'value'])
                    st.altair_chart(chart, use_container_width=True)
                
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
                    
                    # Plot predictions vs actual
                    results_df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
                    chart = alt.Chart(results_df.reset_index()).mark_line().encode(
                        x='index:Q',
                        y=alt.Y('value:Q', title=target_feature),
                        color='variable:N'
                    ).transform_fold(['Actual', 'Predicted'], as_=['variable', 'value'])
                    st.altair_chart(chart, use_container_width=True)
            
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
                corr_df = pd.DataFrame({'Feature': target_corr.index, 'Correlation': target_corr.values})
                st.dataframe(corr_df, use_container_width=True)
                
                # Heatmap
                chart = alt.Chart(corr_df).mark_bar().encode(
                    x=alt.X('Correlation:Q', scale=alt.Scale(domain=[-1, 1])),
                    y=alt.Y('Feature:N', sort='-x'),
                    color=alt.Color('Correlation:Q', scale=alt.Scale(scheme='redblue', domain=[-1, 1]))
                )
                st.altair_chart(chart, use_container_width=True)
            
            elif method == "Seasonal Decomposition":
                progress_bar.progress(0.3)
                status_text.text("Performing seasonal decomposition...")
                
                decomposition = run_seasonal_decomposition(combined_df, target_feature)
                
                if decomposition is None:
                    st.error("Not enough data for seasonal decomposition (need at least 48 observations).")
                    return
                
                progress_bar.progress(1.0)
                status_text.text("Decomposition complete!")
                
                st.success(f"Analysis complete in {time.time() - start_time:.2f}s")
                
                # Plot components
                components = ['observed', 'trend', 'seasonal', 'resid']
                for component in components:
                    data = getattr(decomposition, component)
                    df_plot = pd.DataFrame({'datetime': data.index, 'value': data.values})
                    
                    chart = alt.Chart(df_plot).mark_line().encode(
                        x='datetime:T',
                        y='value:Q'
                    ).properties(title=component.title())
                    
                    st.altair_chart(chart, use_container_width=True)
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > TIMEOUT_SECONDS:
                st.warning(f"Training exceeded 30-minute limit ({elapsed/60:.1f} min)")
        
        except Exception as e:
            status_text.text("")
            progress_bar.empty()
            st.error(f"Error during experimentation: {str(e)}")
