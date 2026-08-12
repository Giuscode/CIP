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

# Coordinate dei quartieri di Pescara
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

# Configurazione pagina
st.set_page_config(
    page_title="CIP | Palantir Tactical HUD",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALANTIR GOTHAM CUSTOM CSS ---
st.markdown("""
    <style>
    /* Dark Background & General Style */
    .stApp {
        background-color: #090D16;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Tactical Bar */
    .tactical-header {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
        border-left: 4px solid #00F2FE;
        padding: 15px 20px;
        border-radius: 6px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    .tactical-title {
        font-family: 'Courier New', monospace;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 2px;
        color: #00F2FE;
        margin: 0;
    }
    
    .tactical-subtitle {
        font-size: 12px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Metric Cards Palantir Style */
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid #1E293B;
        border-top: 2px solid #00F2FE;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }

    div[data-testid="stMetricLabel"] {
        font-family: 'Courier New', monospace;
        color: #94A3B8 !important;
        font-size: 11px !important;
        text-transform: uppercase;
    }

    div[data-testid="stMetricValue"] {
        font-family: 'Courier New', monospace;
        color: #F8FAFC !important;
        font-weight: 700;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }

    /* Expander / Feed Items */
    .streamlit-expanderHeader {
        background-color: #0F172A !important;
        border: 1px solid #1E293B !important;
        border-radius: 6px !important;
        color: #E2E8F0 !important;
        font-family: 'Inter', sans-serif;
    }

    /* Pulse Status Indicator */
    .status-pulse {
        height: 10px;
        width: 10px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #10B981;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown(f"""
    <div class="tactical-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p class="tactical-subtitle"><span class="status-pulse"></span> SYSTEM STATUS: OPERATIONAL | REGION: PESCARA SECTOR</p>
                <h1 class="tactical-title">⚡ C.I.P. // TACTICAL CRIME INTELLIGENCE</h1>
            </div>
            <div style="text-align: right; font-family: 'Courier New', monospace; font-size: 12px; color: #64748B;">
                <div>SYS.TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div>SECURE NODE: T7_ENCRYPTED</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("### 🎛️ RADAR & INGESTION")
limit = st.sidebar.slider("Sensor Depth (Notizie/Fonte):", min_value=1, max_value=25, value=10)
st.sidebar.divider()

if st.sidebar.button("🔄 RUN TACTICAL INGESTION"):
    with st.spinner("Scansione nodi RSS e analisi NLP in corso..."):
        raw_news = fetch_latest_news(limit_per_feed=limit)
        processed = [process_news_item(item) for item in raw_news]
        clean_news = [item for item in processed if item is not None]
        
        _, added = sync_news_with_db(clean_news)
        st.sidebar.success(f"Ingestiti {added} nuovi eventi!")

# --- DATA CARRIAGE ---
all_news = load_database()
district_stats = compute_district_crime_index(all_news)

total_news = len(all_news)
avg_severity = sum(item["severity"] for item in all_news) / total_news if total_news > 0 else 0.0

# --- METRIC TELEMETRY ROW ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="ACTIVE RADAR NODES", value="5 FEEDS", delta="ANSA, Rete8, IlPescara...")
with col2:
    st.metric(label="TOTAL EVENTS LOGGED", value=total_news, delta=f"{len(district_stats)} Zones Mapped")
with col3:
    st.metric(
        label="AVG SEVERITY INDEX", 
        value=f"{avg_severity:.1f} / 10", 
        delta="ELEVATED" if avg_severity > 5 else "NOMINAL",
        delta_color="inverse" if avg_severity > 5 else "normal"
    )
with col4:
    active_districts = sum(1 for d in district_stats.values() if d["total_score"] > 2.0)
    st.metric(label="HIGH-RISK ZONES", value=f"{active_districts} SECTORS", delta="Decay Model On")

st.write("")

# --- MAP & RANKING HUD ---
col_map, col_rank = st.columns([2, 1])

with col_map:
    st.markdown("##### 🗺️ GEOSPATIAL THREAT MATRIX (CARTO DARK)")
    m = folium.Map(
        location=[42.4643, 14.2142], 
        zoom_start=13, 
        tiles="CartoDB dark_matter",
        control_scale=True
    )

    for item in all_news:
        district = item.get("district", "Centro")
        coords = DISTRICT_COORDS.get(district, DISTRICT_COORDS["Centro"])
        base_sev = item.get("severity", 2)
        
        decayed_sev, days_ago = calculate_time_decay_severity(base_sev, item.get("published", ""))
        color = "#FF2A6D" if decayed_sev >= 5 else ("#FFB300" if decayed_sev >= 2 else "#00F2FE")
        
        popup_html = f"""
        <div style='font-family: sans-serif; width: 220px; background-color: #0F172A; color: #F8FAFC; padding: 10px; border-radius: 6px; border: 1px solid #1E293B;'>
            <h4 style='margin:0 0 5px 0; color:#00F2FE; font-family:monospace;'>[{district}]</h4>
            <p style='margin:2px 0; font-size:12px;'><b>Cat:</b> {item['category']}</p>
            <p style='margin:2px 0; font-size:12px;'><b>Severity score:</b> <span style='color:{color}; font-weight:bold;'>{decayed_sev}/10</span></p>
            <p style='margin:2px 0; font-size:10px; color:#94A3B8;'>Age: {days_ago} days ago</p>
            <hr style='border:0; border-top:1px solid #334155; margin:6px 0;'>
            <a href='{item['link']}' target='_blank' style='color:#00F2FE; font-size:11px;'>View Source Document</a>
        </div>
        """
        
        folium.CircleMarker(
            location=coords,
            radius=6 + (decayed_sev * 2),
            popup=folium.Popup(popup_html, max_width=260),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1.5
        ).add_to(m)

    st_folium(m, width="100%", height=420)

with col_rank:
    st.markdown("##### 🏆 SECTOR THREAT RANKING")
    
    sorted_districts = sorted(
        district_stats.items(), 
        key=lambda x: x[1]["total_score"], 
        reverse=True
    )
    
    if not sorted_districts:
        st.info("No tactical data available.")
    else:
        for dist_name, stats in sorted_districts:
            score = stats["total_score"]
            badge = "🔴" if score >= 10 else ("🟡" if score >= 4 else "🔵")
            st.markdown(f"**{badge} {dist_name}**")
            st.progress(min(score / 20.0, 1.0))
            st.caption(f"Threat Score: **{score}** | Logged Incidents: **{stats['news_count']}**")

st.write("---")

# --- VISUAL ANALYTICS SECTION ---
st.markdown("##### 📈 TACTICAL DATA ANALYTICS")

if not all_news:
    st.info("Awaiting news ingestion...")
else:
    df = pd.DataFrame(all_news)

    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown("<p style='font-size:12px; color:#94A3B8;'>INCIDENT DISTRIBUTION BY CATEGORY</p>", unsafe_allow_html=True)
        cat_counts = df['category'].value_counts().reset_index()
        cat_counts.columns = ['Categoria', 'Conteggio']

        chart_cat = alt.Chart(cat_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('Categoria:N', sort='-y', title=None, axis=alt.Axis(labelAngle=-30, labelColor='#94A3B8')),
            y=alt.Y('Conteggio:Q', title="Incidents", axis=alt.Axis(labelColor='#94A3B8')),
            color=alt.value("#FF2A6D")
        ).properties(height=260).configure_view(strokeWidth=0)

        st.altair_chart(chart_cat, use_container_width=True)

    with g_col2:
        st.markdown("<p style='font-size:12px; color:#94A3B8;'>INCIDENT DENSITY BY SECTOR</p>", unsafe_allow_html=True)
        dist_counts = df['district'].value_counts().reset_index()
        dist_counts.columns = ['Quartiere', 'Conteggio']

        chart_dist = alt.Chart(dist_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('Quartiere:N', sort='-y', title=None, axis=alt.Axis(labelAngle=-30, labelColor='#94A3B8')),
            y=alt.Y('Conteggio:Q', title="Incidents", axis=alt.Axis(labelColor='#94A3B8')),
            color=alt.value("#00F2FE")
        ).properties(height=260).configure_view(strokeWidth=0)

        st.altair_chart(chart_dist, use_container_width=True)

st.write("---")

# --- INTELLIGENCE FEED ---
st.markdown("##### 📡 RAW INTELLIGENCE FEED")
if not all_news:
    st.info("Database empty.")
else:
    for item in reversed(all_news):
        base_sev = item['severity']
        decayed_sev, days_ago = calculate_time_decay_severity(base_sev, item.get("published", ""))
        
        badge_color = "🔴" if decayed_sev >= 5 else ("🟡" if decayed_sev >= 2 else "🔵")
        header_text = f"{badge_color} [{item['district']}] {item['title']} — ({days_ago}d ago)"
        
        with st.expander(header_text):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**📍 Sector:** {item['district']}")
            with c2:
                st.write(f"**🏷️ Category:** {item['category']}")
            with c3:
                st.write(f"**⚠️ Severity (Decayed/Base):** {decayed_sev} / {base_sev}")
            
            st.divider()
            st.write(f"**Summary:** {item['summary']}")
            st.write(f"**Source:** {item['source']} | **Timestamp:** {item['published']}")
            st.markdown(f"[Source Article]({item['link']})")