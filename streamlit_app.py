"""
streamlit_app.py - NYPD Shooting Incident Dashboard
"""

import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="NYPD Shootings Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG      = '#161B27'
SURFACE = '#1C2333'
CARD    = '#212D40'
BORDER  = '#2D3A55'
WHITE   = '#E8EAF0'
DIM     = '#7A8BA0'
C1      = '#FF4757'
C2      = '#FFA502'
C3      = '#2ED573'
C4      = '#1E90FF'
C5      = '#A55EEA'

MONTH_ORDER = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
DAY_ORDER   = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@300;400&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] {{ font-family:'DM Sans',sans-serif; background:{BG}; color:{WHITE}; }}
.stApp {{ background-color:{BG}; }}
[data-testid="stSidebar"] {{ background-color:{SURFACE}; border-right:1px solid {BORDER}; }}
[data-testid="stSidebar"] * {{ color:{WHITE} !important; }}
.dash-header {{ padding:28px 0 20px; border-bottom:1px solid {BORDER}; display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:16px; }}
.dash-tag {{ font-family:'DM Mono',monospace; font-size:9px; letter-spacing:3px; color:{C1}; margin-bottom:10px; text-transform:uppercase; }}
.dash-title {{ font-family:'Syne',sans-serif; font-size:34px; font-weight:800; color:{WHITE}; line-height:1.1; }}
.dash-team {{ font-family:'DM Mono',monospace; font-size:10px; color:{DIM}; letter-spacing:1px; margin-top:10px; }}
.dash-yr {{ font-family:'Syne',sans-serif; font-size:28px; font-weight:800; color:{C4}; text-align:right; }}
.dash-meta {{ font-family:'DM Mono',monospace; font-size:9px; color:{DIM}; letter-spacing:1.5px; text-align:right; margin-top:4px; }}
.kpi-card {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:18px 20px; margin-bottom:4px; }}
.kpi-icon {{ font-size:18px; margin-bottom:8px; }}
.kpi-label {{ font-family:'DM Mono',monospace; font-size:9px; letter-spacing:2px; text-transform:uppercase; color:{DIM}; margin-bottom:4px; }}
.kpi-value {{ font-family:'Syne',sans-serif; font-size:26px; font-weight:800; line-height:1; margin-top:4px; font-variant-numeric:tabular-nums; }}
.kpi-red    {{ border-bottom:3px solid {C1}; }} .kpi-red .kpi-value    {{ color:{C1}; }}
.kpi-yellow {{ border-bottom:3px solid {C2}; }} .kpi-yellow .kpi-value {{ color:{C2}; }}
.kpi-blue   {{ border-bottom:3px solid {C4}; }} .kpi-blue .kpi-value   {{ color:{C4}; }}
.kpi-purple {{ border-bottom:3px solid {C5}; }} .kpi-purple .kpi-value {{ color:{C5}; }}
.kpi-green  {{ border-bottom:3px solid {C3}; }} .kpi-green .kpi-value  {{ color:{C3}; }}
div[data-testid="stHorizontalBlock"] > div {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:4px; }}
.block-container {{ padding:0 2rem 2rem; }}
hr {{ border-color:{BORDER} !important; }}
.stSelectbox > div > div {{ background-color:{CARD} !important; border-color:{BORDER} !important; color:{WHITE} !important; }}
.waiting-box {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:48px; text-align:center; margin:40px 0; }}
.filter-label {{ font-family:'DM Mono',monospace; font-size:9px; letter-spacing:2px; color:{DIM}; text-transform:uppercase; margin-bottom:8px; }}
</style>
""", unsafe_allow_html=True)

DB_URL = (f"postgresql://{os.getenv('DB_USER','postgres')}:{os.getenv('DB_PASS','postgres')}"
          f"@{os.getenv('DB_HOST','localhost')}:{os.getenv('DB_PORT','5432')}/{os.getenv('DB_NAME','shootings')}")


@st.cache_resource
def get_engine():
    return create_engine(DB_URL)


def load_data():
    engine = get_engine()
    df = pd.read_sql("""
        SELECT i.incident_key, i.occur_date, i.occur_time,
               i.year, i.month, i.month_name, i.day_of_week, i.hour,
               l.boro, l.precinct, l.loc_of_occur_desc,
               l.loc_classfctn_desc, l.location_desc,
               l.latitude, l.longitude
        FROM incidents i
        LEFT JOIN locations l ON i.location_id = l.location_id
    """, engine)
    df['occur_date']  = pd.to_datetime(df['occur_date'], errors='coerce')
    df['year']        = df['occur_date'].dt.year
    df['month_name']  = df['occur_date'].dt.strftime('%b')
    df['day_of_week'] = df['occur_date'].dt.day_name()
    df['hour']        = pd.to_numeric(df['hour'], errors='coerce')
    return df


def cl(title, height=340):
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans, sans-serif', color=WHITE, size=12),
        title=dict(text=f"<b>{title}</b>",
                   font=dict(family='Syne, sans-serif', size=18, color=WHITE),
                   x=0, xanchor='left'),
        margin=dict(l=10, r=10, t=48, b=10),
        height=height,
        xaxis=dict(gridcolor=BORDER, zerolinecolor='rgba(0,0,0,0)',
                   tickfont=dict(color=WHITE, size=11)),
        yaxis=dict(gridcolor=BORDER, zerolinecolor='rgba(0,0,0,0)',
                   tickfont=dict(color=WHITE, size=11)),
        coloraxis_showscale=False,
        legend=dict(
            font=dict(color=WHITE, size=13, family='DM Sans, sans-serif'),
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
        ),
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<div style='font-family:Syne,sans-serif;font-weight:800;font-size:18px;color:{WHITE};margin-bottom:4px;'>🔴 NYPD Shootings</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:11px;color:{DIM};'>Colglazier · Parajuli<br>Soriano · Sriperambudur</div>", unsafe_allow_html=True)
    st.divider()

# ── Wait for ETL ──────────────────────────────────────────────────────────────
placeholder = st.empty()
for _ in range(60):
    try:
        with get_engine().connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM incidents")).scalar()
        if count and count > 100:
            break
    except Exception:
        pass
    with placeholder.container():
        st.markdown(f'<div class="waiting-box"><div style="font-family:Syne,sans-serif;font-size:24px;font-weight:800;color:{WHITE};margin-bottom:12px;">⏳ ETL Pipeline Running...</div><div style="font-family:DM Sans,sans-serif;font-size:15px;color:{DIM};">Fetching 24,000+ records from NYC Open Data.<br>Takes ~60–90 seconds on first run.</div></div>', unsafe_allow_html=True)
    time.sleep(8)
    st.rerun()
placeholder.empty()

try:
    df = load_data()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if df.empty:
    st.warning("No data. Refresh in a moment.")
    st.stop()

all_years = sorted(df['year'].dropna().unique().astype(int).tolist())
boroughs  = sorted(df['boro'].dropna().unique().tolist())

# Location type — use friendly title-case labels
raw_loc_types = sorted(df['loc_of_occur_desc'].dropna().unique().tolist())
loc_label_map  = {v.title(): v for v in raw_loc_types}   # "Outside" -> "OUTSIDE"
# Remap Inside/Outside -> Indoors/Outdoors for display
DISPLAY_REMAP = {'Outside': 'Outdoors', 'Inside': 'Indoors'}
REVERSE_REMAP = {v: k for k, v in DISPLAY_REMAP.items()}
loc_display    = ['All'] + [DISPLAY_REMAP.get(k, k) for k in loc_label_map.keys()]

# ── Sidebar filters + info ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:9px;letter-spacing:2px;color:{DIM};text-transform:uppercase;margin-bottom:8px;'>Filters</div>", unsafe_allow_html=True)

    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:9px;letter-spacing:2px;color:{DIM};text-transform:uppercase;margin-bottom:4px;'>YEAR RANGE</div>", unsafe_allow_html=True)
    year_range = st.slider(
        "yr", min_value=min(all_years), max_value=max(all_years),
        value=(min(all_years), max(all_years)), label_visibility="collapsed"
    )

    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:9px;letter-spacing:2px;color:{DIM};text-transform:uppercase;margin-top:12px;margin-bottom:4px;'>BOROUGH</div>", unsafe_allow_html=True)
    boro_sel = st.selectbox(
        "boro", options=['All'] + boroughs, index=0, label_visibility="collapsed"
    )

    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:9px;letter-spacing:2px;color:{DIM};text-transform:uppercase;margin-top:12px;margin-bottom:4px;'>LOCATION TYPE</div>", unsafe_allow_html=True)
    loc_sel_label = st.selectbox(
        "loc", options=loc_display, index=0, label_visibility="collapsed"
    )

    st.divider()
    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:9px;letter-spacing:2px;color:{DIM};text-transform:uppercase;margin-bottom:8px;'>Dataset Info</div>", unsafe_allow_html=True)
    st.caption(f"NYC Open Data · {min(all_years)}–{max(all_years)}")
    st.caption("Updated quarterly by NYPD")
    st.markdown(f"**{len(df):,}** total records")
    st.markdown(f"**{df['boro'].nunique()}** boroughs")
    st.markdown(f"**{int(df['precinct'].dropna().nunique())}** precincts")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <div>
        <div class="dash-tag">NYPD · NYC OPEN DATA · 2006–PRESENT</div>
        <div class="dash-title">Shooting Incident<br>Analysis</div>
        <div class="dash-team">Colglazier · Parajuli · Soriano · Sriperambudur  ·  DAEN 328</div>
    </div>
    <div>
        <div class="dash-yr" id="yr-display">2006–2025</div>
        <div class="dash-meta">QUARTERLY UPDATES · SOCRATA API</div>
    </div>
</div>
""", unsafe_allow_html=True)

# (filters moved to sidebar)

# Map selections back to raw values
selected_boros = boroughs if boro_sel == 'All' else [boro_sel]
# Convert display label back to raw DB value
_loc_raw_label = REVERSE_REMAP.get(loc_sel_label, loc_sel_label)
selected_locs  = raw_loc_types if loc_sel_label == 'All' else [loc_label_map.get(_loc_raw_label, _loc_raw_label)]

# ── Filter ────────────────────────────────────────────────────────────────────
mask = (
    df['year'].between(year_range[0], year_range[1]) &
    df['boro'].isin(selected_boros) &
    df['loc_of_occur_desc'].isin(selected_locs)
)
d = df[mask]

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
top_hour   = d['hour'].dropna().astype(int).mode()
peak_month = d['month_name'].mode()
ph = f"{int(top_hour.iloc[0]):02d}:00" if len(top_hour) else "N/A"
pm = peak_month.iloc[0] if len(peak_month) else "N/A"

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f'<div class="kpi-card kpi-red"><div class="kpi-icon">🔴</div><div class="kpi-label">Total Incidents</div><div class="kpi-value">{len(d):,}</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card kpi-yellow"><div class="kpi-icon">🗺️</div><div class="kpi-label">Boroughs</div><div class="kpi-value">{d["boro"].nunique()}</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card kpi-blue"><div class="kpi-icon">🏛️</div><div class="kpi-label">Precincts</div><div class="kpi-value">{int(d["precinct"].dropna().nunique())}</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card kpi-purple"><div class="kpi-icon">🕐</div><div class="kpi-label">Peak Hour</div><div class="kpi-value">{ph}</div></div>', unsafe_allow_html=True)
with k5:
    st.markdown(f'<div class="kpi-card kpi-green"><div class="kpi-icon">📅</div><div class="kpi-label">Peak Month</div><div class="kpi-value">{pm}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══ ROW 1: Yearly + Borough ═══════════════════════════════════════════════════
col1, col2 = st.columns(2)
with col1:
    c = d.groupby('year').size().reset_index(name='count')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=c['year'], y=c['count'], mode='lines+markers',
                             line=dict(color=C1, width=2.5), marker=dict(size=6, color=C1),
                             fill='tozeroy', fillcolor='rgba(255,71,87,0.08)'))
    fig.update_layout(**cl('INCIDENTS PER YEAR'), yaxis_title='Incidents')
    fig.update_xaxes(tickformat='d')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    bc = d['boro'].value_counts().reset_index()
    bc.columns = ['boro','count']
    fig = px.bar(bc, x='boro', y='count', color='count',
                 color_continuous_scale=[CARD, C1])
    fig.update_layout(**cl('INCIDENTS BY BOROUGH'), xaxis_title='', yaxis_title='Incidents')
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

# ══ ROW 2: Monthly + Hour ═════════════════════════════════════════════════════
col3, col4 = st.columns(2)
with col3:
    m = d.groupby('month_name').size().reindex(MONTH_ORDER).reset_index(name='count')
    fig = px.bar(m, x='month_name', y='count', color='count',
                 color_continuous_scale=[CARD, C2])
    fig.update_layout(**cl('SEASONAL TREND — BY MONTH'), xaxis_title='', yaxis_title='Incidents')
    st.plotly_chart(fig, use_container_width=True)

with col4:
    h = d['hour'].dropna().astype(int).value_counts().sort_index().reset_index()
    h.columns = ['hour','count']
    fig = px.bar(h, x='hour', y='count', color='count',
                 color_continuous_scale=[CARD, C5])
    fig.update_layout(**cl('INCIDENTS BY HOUR OF DAY'), xaxis_title='Hour (24h)', yaxis_title='Incidents')
    fig.update_xaxes(tickmode='linear', dtick=2)
    st.plotly_chart(fig, use_container_width=True)

# ══ ROW 3: Location classification + Day of week ══════════════════════════════
col5, col6 = st.columns(2)
with col5:
    lc = d['loc_classfctn_desc'].dropna().value_counts().head(8).sort_values().reset_index()
    lc.columns = ['type','count']
    fig = px.bar(lc, x='count', y='type', orientation='h',
                 color='count', color_continuous_scale=[CARD, C3])
    fig.update_layout(**cl('TOP LOCATION CLASSIFICATIONS'), yaxis_title='', xaxis_title='Incidents')
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

with col6:
    dow = d['day_of_week'].value_counts().reindex(DAY_ORDER).reset_index()
    dow.columns = ['day','count']
    fig = px.bar(dow, x='day', y='count', color='count',
                 color_continuous_scale=[CARD, C4])
    fig.update_layout(**cl('INCIDENTS BY DAY OF WEEK'), xaxis_title='', yaxis_title='Incidents')
    st.plotly_chart(fig, use_container_width=True)

# ══ ROW 4: Borough pie + Inside/Outside ═══════════════════════════════════════
col7, col8 = st.columns(2)

with col7:
    bp = d['boro'].value_counts().reset_index()
    bp.columns = ['boro','count']
    fig = px.pie(bp, names='boro', values='count',
                 color_discrete_sequence=[C1,C2,C3,C4,C5,'#FF6348'])
    fig.update_traces(
        textfont=dict(color=WHITE, size=14, family='DM Sans, sans-serif'),
        insidetextfont=dict(color=WHITE, size=14),
        outsidetextfont=dict(color=WHITE, size=14),
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title=dict(text='<b>BOROUGH SHARE</b>',
                   font=dict(family='Syne, sans-serif', size=18, color=WHITE),
                   x=0, xanchor='left'),
        height=340,
        margin=dict(l=10, r=10, t=48, b=10),
        font=dict(color=WHITE, size=13, family='DM Sans, sans-serif'),
        legend=dict(
            font=dict(color=WHITE, size=13, family='DM Sans, sans-serif'),
            bgcolor='rgba(0,0,0,0)',
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

with col8:
    # Use title-case labels for Inside/Outside
    io_raw = d['loc_of_occur_desc'].dropna()
    io = io_raw.value_counts().reset_index()
    io.columns = ['location','count']
    io['location'] = io['location'].str.title()   # "OUTSIDE" -> "Outside"
    io['location'] = io['location'].map(lambda x: DISPLAY_REMAP.get(x, x))  # "Outside" -> "Outdoors"

    if io.empty:
        st.info("No location type data for current filter selection.")
    else:
        fig = px.pie(io, names='location', values='count',
                     color_discrete_sequence=[C4,C1,C3,C2,C5])
        fig.update_traces(
            textfont=dict(color=WHITE, size=14, family='DM Sans, sans-serif'),
            insidetextfont=dict(color=WHITE, size=14),
            outsidetextfont=dict(color=WHITE, size=14),
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(text='<b>INDOORS VS OUTDOORS</b>',
                       font=dict(family='Syne, sans-serif', size=18, color=WHITE),
                       x=0, xanchor='left'),
            height=340,
            margin=dict(l=10, r=10, t=48, b=10),
            font=dict(color=WHITE, size=13, family='DM Sans, sans-serif'),
            legend=dict(
                font=dict(color=WHITE, size=13, family='DM Sans, sans-serif'),
                bgcolor='rgba(0,0,0,0)',
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

# ══ ROW 5: Top precincts ══════════════════════════════════════════════════════
prec = d['precinct'].dropna().astype(int).value_counts().head(15).sort_values().reset_index()
prec.columns = ['precinct','count']
prec['precinct'] = 'Precinct ' + prec['precinct'].astype(str)
fig = px.bar(prec, x='count', y='precinct', orientation='h',
             color='count', color_continuous_scale=[CARD, C2])
fig.update_layout(**cl('TOP 15 PRECINCTS BY INCIDENT COUNT', height=480),
                  xaxis_title='Incidents', yaxis_title='')
fig.update_traces(marker_line_width=0)
st.plotly_chart(fig, use_container_width=True)

# ══ ROW 6: Map ════════════════════════════════════════════════════════════════
map_df = d.dropna(subset=['latitude','longitude'])
map_df = map_df.sample(min(5000, len(map_df)), random_state=42)

if map_df.empty:
    st.info("No location data available for map.")
else:
    fig = px.scatter_map(
        map_df, lat='latitude', lon='longitude',
        color='boro', opacity=0.55, zoom=10,
        map_style='carto-darkmatter',
        color_discrete_sequence=[C1,C2,C3,C4,C5],
        hover_data={'occur_date': True, 'boro': True,
                    'loc_classfctn_desc': True,
                    'latitude': False, 'longitude': False},
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans, sans-serif', color=WHITE, size=12),
        title=dict(text='<b>INCIDENT MAP (sample of 5,000)</b>',
                   font=dict(family='Syne, sans-serif', size=18, color=WHITE),
                   x=0, xanchor='left'),
        margin=dict(l=10, r=10, t=48, b=10),
        height=520,
        map=dict(center=dict(lat=40.7128, lon=-74.0060)),
        legend=dict(
            font=dict(color=WHITE, size=13, family='DM Sans, sans-serif'),
            bgcolor='rgba(0,0,0,0)',
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("NYPD Shooting Incident Data · NYC Open Data · DAEN 328 · Colglazier · Parajuli · Soriano · Sriperambudur")