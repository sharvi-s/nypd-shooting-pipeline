# NYPD Shooting Incident Data Pipeline
Texas A&M University - DAEN 328 Spring 2026  
Team: William Colglazier, Mallika Parajuli, Ryan Soriano, Sharvi Sriperambudur

---

## Overview
For our term project we built a full stack data engineering pipeline using NYPD shooting incident data pulled live from the NYC Open Data API. The goal was to simulate a real-world data pipeline from raw API data all the way to an interactive dashboard, with everything running in Docker so anyone can spin it up with one command.

Dataset: 23,000+ shooting incidents across NYC from 2006 to present  
Source: [NYC Open Data](https://data.cityofnewyork.us/Public-Safety/Shootings-2006-Present-/5ucz-vwe8)  
Updates: Quarterly by NYPD

---

## How it Works

**1. Extract**  
Hits the Socrata REST API and paginates through all records, saving the raw response to CSV.

**2. Transform**  
Runs 10 modular cleaning functions on the data, each handling one task: parsing dates, standardizing borough names, casting types, dropping duplicates, deriving time features and more.

**3. Load**  
Creates a normalized PostgreSQL schema and loads the cleaned data into two tables, incidents and locations.

**4. Visualize**  
Connects to the database and serves an interactive Streamlit dashboard with 10 charts, sidebar filters and a live incident map of NYC.

---

## Running the Project

```bash
git clone https://github.com/sharvi-s/nypd-shooting-pipeline.git
cd nypd-shooting-pipeline
cp .env.sample .env
docker-compose up --build
```

Open http://localhost:8501 in your browser. The first run takes about 90 seconds to fetch and load all the data, after that it starts instantly.

---

## Stack
Python, PostgreSQL, SQLAlchemy, Streamlit, Plotly, Docker, NYC Open Data