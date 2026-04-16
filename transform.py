"""
transform.py
------------
Cleaning functions for the NYPD Shooting Incident dataset.
Each function handles exactly one cleaning task.

Actual columns:
  INCIDENT_KEY, OCCUR_DATE, OCCUR_TIME, BORO, LOC_OF_OCCUR_DESC,
  PRECINCT, JURISDICTION_CODE, LOC_CLASSFCTN_DESC, LOCATION_DESC,
  X_COORD_CD, Y_COORD_CD, Latitude, Longitude
"""

import pandas as pd
import os


# ── 1. Parse Dates ─────────────────────────────────────────────────────────────
def parse_dates(df):
    """Convert OCCUR_DATE from MM/DD/YYYY string to datetime."""
    df = df.copy()
    df["OCCUR_DATE"] = pd.to_datetime(df["OCCUR_DATE"], errors="coerce")
    return df


# ── 2. Parse Time ──────────────────────────────────────────────────────────────
def parse_time(df):
    """Standardize OCCUR_TIME to HH:MM format."""
    df = df.copy()
    df["OCCUR_TIME"] = pd.to_datetime(
        df["OCCUR_TIME"], format="%H:%M:%S", errors="coerce"
    ).dt.strftime("%H:%M")
    return df


# ── 3. Normalize Capitalization ────────────────────────────────────────────────
def normalize_capitalization(df):
    """Title-case all object/string columns."""
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip().str.title()
    return df


# ── 4. Replace Unknown / Null Placeholders ─────────────────────────────────────
def replace_unknowns(df):
    """Replace '(null)', empty strings, and common null sentinels with pd.NA."""
    df = df.copy()
    placeholders = ["(Null)", "Unknown", "U", "", "None", "Na", "N/A", "nan"]
    df = df.replace(placeholders, pd.NA)
    return df


# ── 5. Cast Coordinates to Float ──────────────────────────────────────────────
def cast_coordinates(df):
    """Convert Latitude, Longitude, X_COORD_CD, Y_COORD_CD to numeric."""
    df = df.copy()
    for col in ["Latitude", "Longitude", "X_COORD_CD", "Y_COORD_CD"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ── 6. Cast Precinct to Integer ────────────────────────────────────────────────
def cast_precinct(df):
    """Convert PRECINCT to integer."""
    df = df.copy()
    if "PRECINCT" in df.columns:
        df["PRECINCT"] = pd.to_numeric(df["PRECINCT"], errors="coerce").astype("Int64")
    return df


# ── 7. Normalize Borough Names ─────────────────────────────────────────────────
def normalize_borough(df):
    """Standardize BORO to consistent title case full names."""
    df = df.copy()
    mapping = {
        "Bronx":         "The Bronx",
        "The Bronx":     "The Bronx",
        "Brooklyn":      "Brooklyn",
        "Manhattan":     "Manhattan",
        "Queens":        "Queens",
        "Staten Island": "Staten Island",
    }
    if "BORO" in df.columns:
        df["BORO"] = df["BORO"].map(mapping).fillna(df["BORO"])
    return df


# ── 8. Derive Time Features ────────────────────────────────────────────────────
def derive_time_features(df):
    """Add YEAR, MONTH, MONTH_NAME, DAY_OF_WEEK, HOUR derived columns."""
    df = df.copy()
    df["YEAR"]        = df["OCCUR_DATE"].dt.year
    df["MONTH"]       = df["OCCUR_DATE"].dt.month
    df["MONTH_NAME"]  = df["OCCUR_DATE"].dt.strftime("%b")
    df["DAY_OF_WEEK"] = df["OCCUR_DATE"].dt.day_name()
    df["HOUR"]        = pd.to_datetime(
        df["OCCUR_TIME"], format="%H:%M", errors="coerce"
    ).dt.hour
    return df


# ── 9. Drop Full Duplicates ────────────────────────────────────────────────────
def drop_duplicates(df):
    """Remove exact duplicate rows."""
    before = len(df)
    df = df.drop_duplicates(subset=["INCIDENT_KEY"]).reset_index(drop=True)
    print(f"    drop_duplicates: removed {before - len(df)} duplicate rows")
    return df


# ── 10. Sort Chronologically ───────────────────────────────────────────────────
def sort_chronologically(df):
    """Sort by OCCUR_DATE ascending."""
    return df.sort_values("OCCUR_DATE").reset_index(drop=True)


# ── Run All ────────────────────────────────────────────────────────────────────
def clean(df):
    """Apply all cleaning functions in order."""
    steps = [
        parse_dates,
        parse_time,
        normalize_capitalization,
        replace_unknowns,
        cast_coordinates,
        cast_precinct,
        normalize_borough,
        derive_time_features,
        drop_duplicates,
        sort_chronologically,
    ]
    for fn in steps:
        print(f"  Running {fn.__name__}...")
        df = fn(df)
    return df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    print("Loading raw data...")
    df = pd.read_csv("data/shootings_raw.csv")
    print(f"Raw rows: {len(df):,}")
    print("\nCleaning...")
    df_clean = clean(df)
    df_clean.to_csv("data/shootings_clean.csv", index=False)
    print(f"\nSaved {len(df_clean):,} clean rows → data/shootings_clean.csv")
    print(f"Date range: {df_clean['OCCUR_DATE'].min()} → {df_clean['OCCUR_DATE'].max()}")
