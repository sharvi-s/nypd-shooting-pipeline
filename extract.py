"""
extract.py
----------
Fetches NYPD Shooting Incident Data from the NYC Socrata API.
Saves raw data to data/shootings_raw.csv
"""

import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

API_URL   = "https://data.cityofnewyork.us/resource/5ucz-vwe8.json"
APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN", "")
LIMIT     = 50000
OUTPUT    = "data/shootings_raw.csv"


def fetch_all(url, limit=LIMIT):
    all_records = []
    offset = 0
    while True:
        params = {"$limit": limit, "$offset": offset, "$order": "occur_date ASC"}
        if APP_TOKEN:
            params["$$app_token"] = APP_TOKEN
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        all_records.extend(batch)
        print(f"  Fetched {len(all_records):,} records...")
        if len(batch) < limit:
            break
        offset += limit
    df = pd.DataFrame(all_records)
    df.columns = [c.upper() for c in df.columns]
    df.rename(columns={"LATITUDE": "Latitude", "LONGITUDE": "Longitude"}, inplace=True)
    return df


def main():
    os.makedirs("data", exist_ok=True)
    print("Fetching NYPD Shooting Incident Data from Socrata API...")
    df = fetch_all(API_URL)
    df.to_csv(OUTPUT, index=False)
    print(f"\nSaved {len(df):,} rows → {OUTPUT}")
    print(f"Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
