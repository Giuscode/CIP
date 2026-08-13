import os
import json
import streamlit as st
import folium
import pandas as pd
import altair as alt
from datetime import datetime
from streamlit_folium import st_folium

from scraper import fetch_latest_news
from nlp_engine import process_news_item
from db_manager import sync_news_with_db, load_database
from analytics import compute_district_crime_index, calculate_time_decay_severity

# Coordinate di ripiego per i marker individuali
DISTRICT_COORDS = {
    "Rancitelli": (42.4550, 14.1950),
    "Fontanelle": (42.4380, 14.2050),
    "Centro": (42.4690, 14.2150),
    "Pescara Vecchia": (42.4610, 14.2130),
    "Portanuova": (42.4560, 14.2230),
    "Colli": (42.4750, 14.1900),
    "Zanni": (42.4880, 14.1850),
    "Tiburtina / Villa Redenta": (42.4480, 14.2000),
    "San Silvestro": (42.4180, 14.2400)
}

st.set_page_config(
    page_title="CIP | Palantir Tactical HUD",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Palantir
st.markdown("""
    <style>
    .stApp { background-color: #090D16; color: #E2E8F0; }
    .tactical-header { background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%); border-left: 4px solid #00F2FE; padding: 15px 20px; border-radius: 6px; margin-bottom: 20px; }
    .tactical-title { font-family: monospace; font-size: 24px; font-weight: 800; color: #00F2FE; margin: 0; }
    div[data-testid="stMetric"] { background: rgba(15, 23, 42, 0.75); border: 1px solid #1E293B; border-top: 2px solid #00F2FE; border-radius: 8px; padding: 12px; }
    section[data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #1E293B; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
    <div class="tactical-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p style="font-size:11px; color:#10B981; margin:0;">● SYSTEM STATUS: OPERATIONAL | REGION: PESCARA SECTOR</p>
                <h1 class="tactical-title">⚡ C.I.P. // TACTICAL GEO-POLYGON MATRIX</h1>
            </div>
            <div style="text-align: right; font-family: monospace; font-size: 12px; color: #64748B;">
                <div>SYS.TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 🎛️ RADAR & INGESTION")
limit = st.sidebar.slider("Sensor Depth (Notizie/Fonte):", min_value=1, max_value=25, value=10)
st.sidebar.divider()

if st.sidebar.button("🔄 RUN TACTICAL INGESTION"):
    with st.spinner("Scansione e analisi NLP in corso..."):
        raw_news = fetch_latest_news(limit_per_feed=limit)
        processed = [process_news_item(item) for item in raw_news]
        clean_news = [item for item in processed if item is not None]
        _, added = sync_news_with_db(clean_news)
        st.sidebar.success(f"Ingestiti {added} nuovi eventi!")

# Carica Dati
all_news = load_database()
district_stats = compute_district_crime_index(all_news)

total_news = len(all_news)
avg_severity = sum(item["severity"] for item in all_news) / total_news if total_news > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="ACTIVE RADAR NODES", value="5 FEEDS")
with col2:
    st.metric(label="TOTAL EVENTS LOGGED", value=total_news)
with col3:
    st.metric(label="AVG SEVERITY INDEX", value=f"{avg_severity:.1f} / 10")
with col4:
    active_districts = sum(1 for d in district_stats.values() if d["total_score"] > 2.0)
    st.metric(label="HIGH-RISK SECTORS", value=f"{active_districts} ZONES")

st.write("")

# Mappa e Ranking
col_map, col_rank = st.columns([2, 1])

with col_map:
    st.markdown("##### 🗺️ POLYGON THREAT MAP (CARTO DARK)")
    m = folium.Map(location=[42.4643, 14.2142], zoom_start=13, tiles="CartoDB dark_matter")

    # Carica e disegna i Poligoni GeoJSON
    geojson_path = os.path.join("data", "pescara_districts.geojson")
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        def style_function(feature):
            district_name = feature["properties"]["name"]
            score = district_stats.get(district_name, {}).get("total_score", 0.0)
            
            # Assegnazione colore in base allo score accumulato del settore
            if score >= 10.0:
                fill_color = "#FF2A6D"  # Rosso neon per alto rischio
                fill_opacity = 0.5
            elif score >= 4.0:
                fill_color = "#FFB300"  # Giallo/Arancio per rischio medio
                fill_opacity = 0.4
            elif score > 0:
                fill_color = "#00F2FE"  # Azzurro per basso rischio
                fill_opacity = 0.25
            else:
                fill_color = "#334155"  # Grigio per nessuna minaccia
                fill_opacity = 0.1

            return {
                "fillColor": fill_color,
                "color": fill_color,
                "weight": 2,
                "fillOpacity": fill_opacity
            }

        folium.GeoJson(
            geojson_data,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Settore:"], localize=True)
        ).add_to(m)

    # Disegna comunque i cerchi dei singoli eventi sopra i poligoni
    for item in all_news:
        district = item.get("district", "Centro")
        coords = DISTRICT_COORDS.get(district, DISTRICT_COORDS["Centro"])
        base_sev = item.get("severity", 2)
        decayed_sev, days_ago = calculate_time_decay_severity(base_sev, item.get("published", ""))
        color = "#FF2A6D" if decayed_sev >= 5 else ("#FFB300" if decayed_sev >= 2 else "#00F2FE")
        
        popup_html = f"<b>[{district}]</b><br>{item['category']}<br>Score: {decayed_sev}/10"
        
        folium.CircleMarker(
            location=coords,
            radius=4 + (decayed_sev * 1.5),
            popup=popup_html,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            weight=1
        ).add_to(m)

    st_folium(m, width="100%", height=420)

with col_rank:
    st.markdown("##### 🏆 SECTOR THREAT RANKING")
    sorted_districts = sorted(district_stats.items(), key=lambda x: x[1]["total_score"], reverse=True)
    if not sorted_districts:
        st.info("Nessun dato tattico disponibile.")
    else:
        for dist_name, stats in sorted_districts:
            score = stats["total_score"]
            badge = "🔴" if score >= 10 else ("🟡" if score >= 4 else "🔵")
            st.markdown(f"**{badge} {dist_name}**")
            st.progress(min(score / 20.0, 1.0))
            st.caption(f"Score: **{score}** | Eventi: **{stats['news_count']}**")

st.write("---")

# Feed e Analytics
st.markdown("##### 📡 RAW INTELLIGENCE FEED")
if not all_news:
    st.info("Database vuoto.")
else:
    for item in reversed(all_news):
        base_sev = item['severity']
        decayed_sev, days_ago = calculate_time_decay_severity(base_sev, item.get("published", ""))
        badge_color = "🔴" if decayed_sev >= 5 else ("🟡" if decayed_sev >= 2 else "🔵")
        
        with st.expander(f"{badge_color} [{item['district']}] {item['title']} — ({days_ago}d ago)"):
            st.write(f"**Categoria:** {item['category']} | **Score:** {decayed_sev}/10")
            st.write(f"**Sommario:** {item['summary']}")
            st.markdown(f"[Documento Fonte]({item['link']})")