"""
load.py
-------
Full ETL: Extract -> Transform -> Load into PostgreSQL.
Uses a FLAT schema — one incidents table, one locations table,
joined by a simple sequential location_id. No complex merge.
"""

import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from extract import fetch_all, API_URL
from transform import clean

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "shootings")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    return create_engine(DATABASE_URL)


def wait_for_db(engine, retries=20, delay=3):
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database is ready.")
            return
        except Exception:
            print(f"  Waiting for database... ({i+1}/{retries})")
            time.sleep(delay)
    raise RuntimeError("Database not available after waiting.")


def already_loaded(engine):
    try:
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM incidents")).scalar()
            return count > 100
    except Exception:
        return False


def create_schema(engine):
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS incidents CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS locations CASCADE"))
        conn.execute(text("""
            CREATE TABLE locations (
                location_id        SERIAL PRIMARY KEY,
                boro               TEXT,
                precinct           INTEGER,
                jurisdiction_code  INTEGER,
                loc_of_occur_desc  TEXT,
                loc_classfctn_desc TEXT,
                location_desc      TEXT,
                x_coord            INTEGER,
                y_coord            INTEGER,
                latitude           FLOAT,
                longitude          FLOAT
            )
        """))
        conn.execute(text("""
            CREATE TABLE incidents (
                incident_key TEXT PRIMARY KEY,
                occur_date   DATE,
                occur_time   TEXT,
                location_id  INTEGER REFERENCES locations(location_id),
                year         INTEGER,
                month        INTEGER,
                month_name   TEXT,
                day_of_week  TEXT,
                hour         INTEGER
            )
        """))
        conn.commit()
    print("Schema created.")


def load_all(df, engine):
    """Load locations then incidents using row index as location_id — no merge needed."""

    df = df.reset_index(drop=True)
    df['location_id'] = df.index + 1  # simple sequential ID

    # ── Locations ──────────────────────────────────────────────────────────────
    loc_col_map = {
        'BORO':               'boro',
        'PRECINCT':           'precinct',
        'JURISDICTION_CODE':  'jurisdiction_code',
        'LOC_OF_OCCUR_DESC':  'loc_of_occur_desc',
        'LOC_CLASSFCTN_DESC': 'loc_classfctn_desc',
        'LOCATION_DESC':      'location_desc',
        'X_COORD_CD':         'x_coord',
        'Y_COORD_CD':         'y_coord',
        'Latitude':           'latitude',
        'Longitude':          'longitude',
    }
    loc_cols = {k: v for k, v in loc_col_map.items() if k in df.columns}
    locations = df[['location_id'] + list(loc_cols.keys())].copy()
    locations = locations.rename(columns=loc_cols)

    for col in ['precinct', 'jurisdiction_code', 'x_coord', 'y_coord']:
        if col in locations.columns:
            locations[col] = pd.to_numeric(locations[col], errors='coerce')
    for col in ['latitude', 'longitude']:
        if col in locations.columns:
            locations[col] = pd.to_numeric(locations[col], errors='coerce')

    locations.to_sql('locations', engine, if_exists='append', index=False,
                     method='multi', chunksize=500)
    print(f"  Loaded {len(locations):,} location records.")

    # ── Incidents ──────────────────────────────────────────────────────────────
    inc_col_map = {
        'INCIDENT_KEY': 'incident_key',
        'OCCUR_DATE':   'occur_date',
        'OCCUR_TIME':   'occur_time',
        'YEAR':         'year',
        'MONTH':        'month',
        'MONTH_NAME':   'month_name',
        'DAY_OF_WEEK':  'day_of_week',
        'HOUR':         'hour',
    }
    inc_cols = {k: v for k, v in inc_col_map.items() if k in df.columns}
    incidents = df[['location_id'] + list(inc_cols.keys())].copy()
    incidents = incidents.rename(columns=inc_cols)
    incidents = incidents.drop_duplicates(subset=['incident_key'])
    incidents['occur_date'] = pd.to_datetime(incidents['occur_date'], errors='coerce')

    incidents.to_sql('incidents', engine, if_exists='append', index=False,
                     method='multi', chunksize=500)
    print(f"  Loaded {len(incidents):,} incident records.")


def main():
    os.makedirs("data", exist_ok=True)
    engine = get_engine()

    print("Waiting for PostgreSQL...")
    wait_for_db(engine)

    if already_loaded(engine):
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM incidents")).scalar()
            boros = conn.execute(text("SELECT COUNT(DISTINCT boro) FROM locations")).scalar()
        print(f"Already loaded: {count:,} incidents, {boros} boroughs. Skipping ETL.")
        return

    create_schema(engine)

    print("\n" + "="*50)
    print("STEP 1: EXTRACT")
    print("="*50)
    df_raw = fetch_all(API_URL)
    df_raw.to_csv("data/shootings_raw.csv", index=False)
    print(f"Raw rows: {len(df_raw):,}")

    print("\n" + "="*50)
    print("STEP 2: TRANSFORM")
    print("="*50)
    df_clean = clean(df_raw)
    df_clean.to_csv("data/shootings_clean.csv", index=False)
    print(f"Clean rows: {len(df_clean):,}")
    print(f"Boroughs in data: {df_clean['BORO'].dropna().unique().tolist()}")

    print("\n" + "="*50)
    print("STEP 3: LOAD -> PostgreSQL")
    print("="*50)
    load_all(df_clean, engine)

    with engine.connect() as conn:
        n_inc  = conn.execute(text("SELECT COUNT(*) FROM incidents")).scalar()
        n_loc  = conn.execute(text("SELECT COUNT(*) FROM locations")).scalar()
        boros  = conn.execute(text("SELECT COUNT(DISTINCT boro) FROM locations")).scalar()
        precs  = conn.execute(text("SELECT COUNT(DISTINCT precinct) FROM locations")).scalar()

    print(f"\nDone!")
    print(f"  incidents : {n_inc:,}")
    print(f"  locations : {n_loc:,}")
    print(f"  boroughs  : {boros}")
    print(f"  precincts : {precs}")


if __name__ == "__main__":
    main()