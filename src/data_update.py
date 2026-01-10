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
    df = df.fillna(0)
    # Get Supabase client
    supabase = get_supabase()
    # Convert DataFrame to list of dicts for Supabase
    records = df.to_dict(orient='records')
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        response = supabase.table('carbon_intensity').upsert(batch).execute()
        if hasattr(response, 'status_code') and response.status_code >= 300:
            print(f"Error uploading batch {i//batch_size+1}: {response}")
        else:
            print(f"Batch {i//batch_size+1} uploaded successfully.")

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
        response = supabase.table('weather').upsert(batch).execute()
        if hasattr(response, 'status_code') and response.status_code >= 300:
            print(f"Error uploading weather batch {i//batch_size+1}: {response}")
        else:
            print(f"Weather batch {i//batch_size+1} uploaded successfully.")