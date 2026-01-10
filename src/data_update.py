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
