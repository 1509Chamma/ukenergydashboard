REGION_COORDS = {
    1: ("North Scotland", 57.5, -4.5),
    2: ("South Scotland", 55.9, -3.2),
    3: ("North West England", 53.8, -2.6),
    4: ("North East England", 54.9, -1.6),
    5: ("South Yorkshire", 53.5, -1.5),
    6: ("North Wales & Merseyside", 53.2, -3.0),
    7: ("South Wales", 51.6, -3.4),
    8: ("West Midlands", 52.5, -2.0),
    9: ("East Midlands", 52.8, -1.0),
    10: ("East England", 52.2, 0.9),
    11: ("South West England", 50.7, -3.5),
    12: ("South England", 51.0, -1.3),
    13: ("London", 51.5, -0.1),
    14: ("South East England", 51.3, 0.5),
}
import pandas as pd
import requests
from datetime import datetime, date
from supabase_client import get_supabase

def is_today_data_missing():
    """Check if there is missing carbon intensity data for any day in the past month in Supabase."""
    supabase = get_supabase()
    today = date.today()
    month_ago = today.replace(day=1)  # Start of this month
    # Get all unique datetimes in the last month
    response = supabase.table('carbon_intensity').select('datetime').gte('datetime', month_ago.strftime('%Y-%m-%d')).execute()
    existing_dates = set()
    if hasattr(response, 'data') and response.data:
        for row in response.data:
            dt = row.get('datetime')
            if dt:
                existing_dates.add(str(dt)[:10])
    # Check for each day in the range
    for i in range((today - month_ago).days + 1):
        day = (month_ago + pd.Timedelta(days=i)).strftime('%Y-%m-%d')
        if day not in existing_dates:
            return True  # Missing at least one day
    return False

def update_and_upload_carbon_data():
    """Fetch carbon intensity data from an API and upload to Supabase if today's data is missing."""
    if not is_today_data_missing():
        return  # No update needed
    API_URL = "https://api.carbonintensity.org.uk/regional"
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Could not fetch carbon data from API: {e}")
        return
    # Parse API response to DataFrame (adjust as needed for actual API structure)
    try:
        records = []
        for region in data['data'][0]['regions']:
            record = {
                'datetime': data['data'][0]['from'],
                'region_id': region.get('regionid'),
                'region_name': region.get('shortname'),
                'forecast': region.get('intensity', {}).get('forecast'),
                'index': region.get('intensity', {}).get('index'),
            }
            for gen in region.get('generationmix', []):
                fuel = gen.get('fuel', '').lower().replace(' ', '_')
                record[f'gen_{fuel}'] = gen.get('perc')
            records.append(record)
        df = pd.DataFrame(records)
    except Exception as e:
        print(f"Error parsing API data: {e}")
        return
    # Clean and format
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Only fill NaN in generation columns with 0, don't fill forecast/index
    gen_cols = [col for col in df.columns if col.startswith('gen_')]
    df[gen_cols] = df[gen_cols].fillna(0)
    
    # Filter out records with invalid forecast or index (should have actual values, not 0 or NaN)
    df = df[(df['forecast'].notna()) & (df['forecast'] != 0) | (df['index'].notna())]
    
    if df.empty:
        print("No valid carbon data to upload after validation")
        return
    
    print(f"Uploading {len(df)} valid carbon records")
    # Get Supabase client
    supabase = get_supabase()
    # Convert DataFrame to list of dicts for Supabase
    records = df.to_dict(orient='records')
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            response = supabase.table('carbon_intensity').upsert(batch, ignore_duplicates=False).execute()
            if hasattr(response, 'status_code') and response.status_code >= 300:
                print(f"Error uploading batch {i//batch_size+1}: {response}")
            else:
                print(f"Batch {i//batch_size+1} uploaded successfully.")
        except Exception as e:
            # If it's a duplicate key error, that's okay - data already exists
            if '23505' in str(e) or 'duplicate' in str(e).lower():
                print(f"Batch {i//batch_size+1}: Data already up to date")
            else:
                print(f"Error uploading batch {i//batch_size+1}: {e}")

def is_weather_data_missing():
    """Check if there is missing weather data for any day in the past month in Supabase."""
    supabase = get_supabase()
    today = date.today()
    month_ago = today.replace(day=1)
    response = supabase.table('weather').select('datetime').gte('datetime', month_ago.strftime('%Y-%m-%d')).execute()
    existing_dates = set()
    if hasattr(response, 'data') and response.data:
        for row in response.data:
            dt = row.get('datetime')
            if dt:
                existing_dates.add(str(dt)[:10])
    for i in range((today - month_ago).days + 1):
        day = (month_ago + pd.Timedelta(days=i)).strftime('%Y-%m-%d')
        if day not in existing_dates:
            return True
    return False

def update_and_upload_weather_data():
    """Fetch weather data for all regions from Open-Meteo API and upload to Supabase if any day in the past month is missing."""
    if not is_weather_data_missing():
        return  # No update needed
    today = date.today()
    month_ago = today.replace(day=1)
    all_records = []
    for region_id, (name, lat, lon) in REGION_COORDS.items():
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": month_ago.strftime('%Y-%m-%d'),
            "end_date": today.strftime('%Y-%m-%d'),
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover,precipitation",
            "timezone": "Europe/London"
        }
        try:
            response = requests.get(url, params=params, timeout=120)
            response.raise_for_status()
            data = response.json()
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            for i, t in enumerate(times):
                all_records.append({
                    'datetime': t,
                    'region_id': region_id,
                    'region_name': name,
                    'temperature': hourly.get('temperature_2m', [None]*len(times))[i],
                    'humidity': hourly.get('relative_humidity_2m', [None]*len(times))[i],
                    'wind_speed': hourly.get('wind_speed_10m', [None]*len(times))[i],
                    'cloud_cover': hourly.get('cloud_cover', [None]*len(times))[i],
                    'precipitation': hourly.get('precipitation', [None]*len(times))[i],
                })
            print(f"{name}: {len(times):,} records")
        except Exception as e:
            print(f"Error fetching weather for {name}: {e}")
    if not all_records:
        print("No weather data fetched.")
        return
    df = pd.DataFrame(all_records)
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    df = df.fillna(0)
    supabase = get_supabase()
    records = df.to_dict(orient='records')
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            response = supabase.table('weather').upsert(batch, ignore_duplicates=False).execute()
            if hasattr(response, 'status_code') and response.status_code >= 300:
                print(f"Error uploading weather batch {i//batch_size+1}: {response}")
            else:
                print(f"Weather batch {i//batch_size+1} uploaded successfully.")
        except Exception as e:
            # If it's a duplicate key error, that's okay - data already exists
            if '23505' in str(e) or 'duplicate' in str(e).lower():
                print(f"Weather batch {i//batch_size+1}: Data already up to date")
            else:
                print(f"Error uploading weather batch {i//batch_size+1}: {e}")

def is_demand_data_missing():
    """Check if there is missing demand data for any day in the past month in Supabase."""
    supabase = get_supabase()
    today = date.today()
    month_ago = today.replace(day=1)
    response = supabase.table('historic_demand').select('datetime').gte('datetime', month_ago.strftime('%Y-%m-%d')).execute()
    existing_dates = set()
    if hasattr(response, 'data') and response.data:
        for row in response.data:
            dt = row.get('datetime')
            if dt:
                existing_dates.add(str(dt)[:10])
    for i in range((today - month_ago).days + 1):
        day = (month_ago + pd.Timedelta(days=i)).strftime('%Y-%m-%d')
        if day not in existing_dates:
            return True
    return False

def update_and_upload_demand_data():
    """Fetch demand data from NESO API and upload to Supabase if newer data is available."""
    supabase = get_supabase()
    
    # Get the latest datetime already in the database
    try:
        response = supabase.table('historic_demand').select('datetime').order('datetime', desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            latest_date = pd.to_datetime(response.data[0]['datetime'])
            start_date = latest_date + pd.Timedelta(hours=1)  # Query from one hour after latest
            print(f"Latest demand data in DB: {latest_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"Fetching demand data from: {start_date.strftime('%Y-%m-%d %H:%M')}")
        else:
            # No data in DB, fetch from 3 months ago
            start_date = date.today() - pd.Timedelta(days=90)
            print(f"No demand data in DB, fetching from 90 days ago: {start_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error checking latest demand date: {e}")
        start_date = date.today() - pd.Timedelta(days=90)
    
    today = date.today()
    sql_query = f'''SELECT * FROM "b2bde559-3455-4021-b179-dfe60c0337b0" WHERE "SETTLEMENT_DATE" >= '{start_date.strftime('%Y-%m-%d')}T00:00:00.000Z' AND "SETTLEMENT_DATE" <= '{(today + pd.Timedelta(days=1)).strftime('%Y-%m-%d')}T23:59:59.000Z' ORDER BY "SETTLEMENT_DATE" ASC'''
    
    try:
        params = {'sql': sql_query}
        response = requests.get(
            'https://api.neso.energy/api/3/action/datastore_search_sql',
            params=params,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        records = data.get('result', {}).get('records', [])
    except Exception as e:
        print(f"Error fetching demand data from NESO API: {e}")
        return
    
    if not records:
        print("No demand data fetched.")
        return
    
    # Convert to DataFrame and clean
    df = pd.DataFrame(records)
    
    # Rename columns to lowercase with underscores for consistency
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # Remove metadata columns that start with underscore (e.g., _id, _full_text)
    df = df[[col for col in df.columns if not col.startswith('_')]]
    
    # Map settlement_date to datetime for consistency with schema
    if 'settlement_date' in df.columns:
        df['datetime'] = pd.to_datetime(df['settlement_date'])
        df = df.drop(columns=['settlement_date'])
    
    # Fill NaN only in numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    supabase = get_supabase()
    records = df.to_dict(orient='records')
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            response = supabase.table('historic_demand').upsert(batch, ignore_duplicates=False).execute()
            if hasattr(response, 'status_code') and response.status_code >= 300:
                print(f"Error uploading demand batch {i//batch_size+1}: {response}")
            else:
                print(f"Demand batch {i//batch_size+1} uploaded successfully.")
        except Exception as e:
            # If it's a duplicate key error, that's okay - data already exists
            if '23505' in str(e) or 'duplicate' in str(e).lower():
                print(f"Demand batch {i//batch_size+1}: Data already up to date")
            else:
                print(f"Error uploading demand batch {i//batch_size+1}: {e}")
