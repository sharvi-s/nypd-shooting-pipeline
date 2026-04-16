# 🔴 NYPD Shooting Incident Data Pipeline

**DAEN 328 — Term Project Phase 2**  
Texas A&M University · Spring 2025

> A fully dockerized, end-to-end data engineering pipeline that extracts NYPD shooting incident data from the NYC Open Data API, cleans and transforms it, loads it into PostgreSQL, and visualizes it through an interactive Streamlit dashboard.

---

## 👥 Team

| Name | GitHub | Contribution |
|------|--------|-------------|
| William Colglazier | [@wcolglazier](https://github.com) | ETL pipeline, extract.py, Docker setup |
| Mallika Parajuli | [@mparajuli](https://github.com) | transform.py, data cleaning functions |
| Ryan Soriano | [@rsoriano](https://github.com) | load.py, PostgreSQL schema design |
| Sharvi Sriperambudur | [@sharvi](https://github.com) | Streamlit dashboard, docker-compose, README |

---

## 📊 Dataset

- **Source:** [NYC Open Data Portal](https://data.cityofnewyork.us/Public-Safety/Shootings-2006-Present-/5ucz-vwe8)
- **API:** `https://data.cityofnewyork.us/resource/5ucz-vwe8.json`
- **Records:** ~24,000 shooting incidents (2006–present)
- **Update frequency:** Quarterly by NYPD
- **Columns used:** `INCIDENT_KEY`, `OCCUR_DATE`, `OCCUR_TIME`, `BORO`, `LOC_OF_OCCUR_DESC`, `PRECINCT`, `JURISDICTION_CODE`, `LOC_CLASSFCTN_DESC`, `LOCATION_DESC`, `X_COORD_CD`, `Y_COORD_CD`, `Latitude`, `Longitude`

---

## 🏗 Pipeline Architecture

```
NYC Open Data API
       │
       ▼
  extract.py          ← Fetches all records via Socrata REST API (paginated)
       │
       ▼
  transform.py        ← 10 cleaning functions (one task each)
       │
       ▼
  load.py             ← Inserts into PostgreSQL (locations + incidents tables)
       │
       ▼
  streamlit_app.py    ← Interactive dashboard with 8+ visualizations
```

---

## 🗄 PostgreSQL Schema

```sql
locations (
    location_id        SERIAL PRIMARY KEY,
    boro               VARCHAR(50),
    precinct           INTEGER,
    jurisdiction_code  INTEGER,
    loc_of_occur_desc  VARCHAR(100),
    loc_classfctn_desc VARCHAR(100),
    x_coord            INTEGER,
    y_coord            INTEGER,
    latitude           FLOAT,
    longitude          FLOAT
)

incidents (
    incident_key  VARCHAR(50) PRIMARY KEY,
    occur_date    DATE,
    occur_time    VARCHAR(10),
    location_id   INTEGER REFERENCES locations(location_id),
    location_desc VARCHAR(255),
    year          INTEGER,
    month         INTEGER,
    month_name    VARCHAR(10),
    day_of_week   VARCHAR(15),
    hour          INTEGER
)
```

---

## 🧹 Data Cleaning Functions (`transform.py`)

Each function handles exactly one cleaning task:

| # | Function | Description |
|---|----------|-------------|
| 1 | `parse_dates` | Converts `OCCUR_DATE` from `MM/DD/YYYY` to datetime |
| 2 | `parse_time` | Standardizes `OCCUR_TIME` to `HH:MM` format |
| 3 | `normalize_capitalization` | Title-cases all string columns |
| 4 | `replace_unknowns` | Replaces `(null)`, empty strings, `Unknown` with `pd.NA` |
| 5 | `cast_coordinates` | Converts lat/lon/coords to float |
| 6 | `cast_precinct` | Converts precinct to nullable integer |
| 7 | `normalize_borough` | Standardizes borough names (e.g., `BRONX` → `The Bronx`) |
| 8 | `derive_time_features` | Adds `YEAR`, `MONTH`, `MONTH_NAME`, `DAY_OF_WEEK`, `HOUR` |
| 9 | `drop_duplicates` | Removes duplicate `INCIDENT_KEY` rows |
| 10 | `sort_chronologically` | Sorts by `OCCUR_DATE` ascending |

---

## 🚀 Running the Project

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

### 1. Clone the repo
```bash
git clone https://github.com/your-team/nypd-shooting-pipeline.git
cd nypd-shooting-pipeline
```

### 2. Set up environment variables
```bash
cp .env.sample .env
# Edit .env with your preferred DB credentials
```

### 3. Run the full pipeline with one command
```bash
docker-compose up --build
```

This will automatically:
1. Start a **PostgreSQL** container (empty database)
2. Run the **ETL pipeline** — fetch → clean → load data into PostgreSQL
3. Launch the **Streamlit dashboard** at [http://localhost:8501](http://localhost:8501)

### 4. Access the dashboard
Open your browser and go to:
```
http://localhost:8501
```

### Stopping the project
```bash
docker-compose down          # stop containers
docker-compose down -v       # stop and delete database volume
```

---

## 🖥 Running Without Docker (Local Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure .env
cp .env.sample .env

# Run ETL pipeline
python load.py

# Launch dashboard
streamlit run streamlit_app.py
```

---

## 📁 Folder Structure

```
nypd-shooting-pipeline/
├── extract.py          # Step 1 — REST API fetch (paginated Socrata)
├── transform.py        # Step 2 — 10 cleaning functions
├── load.py             # Step 3 — PostgreSQL load (runs full ETL)
├── streamlit_app.py    # Step 4 — Streamlit dashboard
├── Dockerfile          # Docker image for ETL + Streamlit
├── docker-compose.yml  # Orchestrates PostgreSQL + ETL + Streamlit
├── requirements.txt    # Python dependencies
├── .env.sample         # Environment variable template (no secrets)
├── README.md           # This file
└── data/               # Auto-created: raw + clean CSVs
```

---

## 📈 Dashboard Features

The Streamlit dashboard includes **8 interactive visualizations**:

1. **Incidents Per Year** — line chart showing year-over-year trend
2. **Incidents by Borough** — bar chart comparing all 5 boroughs
3. **Borough Share** — donut pie chart of proportional breakdown
4. **Top Location Classifications** — where incidents most commonly occur
5. **Seasonal Trend by Month** — which months have the most incidents
6. **Incidents by Hour of Day** — peak hours for shooting incidents
7. **Incidents by Day of Week** — weekly patterns
8. **Inside vs Outside** — pie chart of location type
9. **Top 15 Precincts** — highest-incident precincts
10. **Geographic Map** — scatter map of incidents across NYC

**Sidebar filters:** Year range slider · Borough multiselect · Location type multiselect

---

## 🐳 Docker Services

| Service | Description | Port |
|---------|-------------|------|
| `db` | PostgreSQL 15 database | 5432 |
| `etl` | Runs extract → transform → load pipeline | — |
| `streamlit` | Streamlit dashboard web app | 8501 |

---

## 🔮 Future Steps

- Add victim/perpetrator demographic tables from supplementary NYPD datasets
- Implement incremental batch updates (only fetch new records since last run)
- Add time-series forecasting for shooting incident predictions
- Deploy to cloud (AWS/GCP) with automated weekly refresh
- Add authentication to the Streamlit dashboard
