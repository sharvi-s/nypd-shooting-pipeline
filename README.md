# NYPD Shooting Incident Data Pipeline
**Texas A&M University - DAEN 328 · Spring 2026**  
**Team:** William Colglazier · Mallika Parajuli · Ryan Soriano · Sharvi Sriperambudur

## Overview
We built a full stack data engineering pipeline using NYPD shooting incident data from the NYC Open Data API. The pipeline extracts, cleans, and loads the data into a PostgreSQL database, which is then visualized through an interactive Streamlit dashboard — all containerized with Docker.

**Dataset:** 23,000+ shooting incidents from 2006 to present  
**API:** https://data.cityofnewyork.us/resource/5ucz-vwe8.json

## Pipeline
Extract: pulls all records from the Socrata API using pagination  
Transform: 10 cleaning functions, each handling one task  
Load: inserts cleaned data into two PostgreSQL tables: incidents and locations  
Visualize:  Streamlit dashboard with filters and 10 charts including a live NYC map

## How to Run
cp .env.sample .env
docker-compose up --build

Open http://localhost:8501

## Stack
Python · PostgreSQL · SQLAlchemy · Streamlit · Plotly · Docker