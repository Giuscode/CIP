import streamlit as st
import folium
import pandas as pd
import altair as alt
from streamlit_folium import st_folium

from scraper import fetch_latest_news
from nlp_engine import process_news_item
from db_manager import sync_news_with_db, load_database
from analytics import compute_district_crime_index, calculate_time_decay_severity

# Coordinate geografiche indicative dei quartieri di Pescara
DISTRICT_COORDS = {
    "Rancitelli": (42.4550, 14.1950),
    "Fontanelle": (42.4380, 14.2050),
    "Centro": (42.4690, 14.2150),
    "Pescara Vecchia": (42.4610, 14.2130),
    "Portanuova": (42.4560, 14.2230),
    "Colli": (42.4750, 14.1900),
    "Zanni": (42.4880, 14.1850),
    "Tiburtina / Villa Redenta": (42.4480, 14.2000),
    "San Silvestro": (42.4180, 14.2400),
    "Pescara (Generico)": (42.4643, 14.2142)
}

# Configurazione della pagina "Palantir Style"
st.set_page_config(
    page_title="C.I.P - Crime Index Pescara",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Applicazione dello stile
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)


# Titolo Dashboard
st.title("C.I.P.: Crime Index Pescara")
st.caption("Sistema iperlocale di monitoraggio e analisi notizie di cronaca")

st.divider()

# Sidebar
st.sidebar.header("⚙️ Pannello di Controllo")
limit = st.sidebar.slider("Notizie da cercare per fonte:", min_value=1, max_value=20, value=10)
st.sidebar.divider()

if st.sidebar.button("🔄 Aggiornamento Notizie"):
    with st.spinner("Scraping e analisi in corso..."):
        raw_news = fetch_latest_news(limit_per_feed=limit)
        processed = [process_news_item(item) for item in raw_news]
        clean_news = [item for item in processed if item is not None]
        
        _, added = sync_news_with_db(clean_news)
        st.sidebar.success(f"Aggiunte {added} nuove notizie al DB!")

# Carica Database e Calcola Metriche
all_news = load_database()
district_stats = compute_district_crime_index(all_news)

total_news = len(all_news)
avg_severity = sum(item["severity"] for item in all_news) / total_news if total_news > 0 else 0.0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Status Sistema", value="Online", delta="Full Analytics Active")
with col2:
    st.metric(label="Notizie in DB", value=total_news, delta=f"{len(district_stats)} Quartieri Mappati")
with col3:
    st.metric(
        label="Severity Media (Storica)", 
        value=f"{avg_severity:.1f} / 10", 
        delta="Livello Allerta" if avg_severity > 5 else "Nella Norma",
        delta_color="inverse" if avg_severity > 5 else "normal"
    )

st.write("---")

# 1. MAPPA & RANKING
col_map, col_rank = st.columns([2, 1])

with col_map:
    st.subheader("🗺️ Mappa Termica Dinamica")
    m = folium.Map(location=[42.4643, 14.2142], zoom_start=13, tiles="CartoDB dark_matter")

    for item in all_news:
        district = item.get("district", "Centro")
        coords = DISTRICT_COORDS.get(district, DISTRICT_COORDS["Centro"])
        base_sev = item.get("severity", 2)
        
        decayed_sev, days_ago = calculate_time_decay_severity(base_sev, item.get("published", ""))
        color = "#ff4b4b" if decayed_sev >= 5 else ("#faca15" if decayed_sev >= 2 else "#3182ce")
        
        popup_html = f"""
        <div style='font-family: sans-serif; width: 220px;'>
            <h4 style='margin-bottom:5px;'>{district}</h4>
            <p><b>Categoria:</b> {item['category']}</p>
            <p><b>Score Origine:</b> {base_sev}/10</p>
            <p><b>Score Attuale:</b> <span style='color:{color}; font-weight:bold;'>{decayed_sev}/10</span></p>
            <p style='font-size:11px; color:gray;'>Età: {days_ago} giorni fa</p>
            <a href='{item['link']}' target='_blank'>Leggi articolo</a>
        </div>
        """
        
        folium.CircleMarker(
            location=coords,
            radius=6 + (decayed_sev * 2),
            popup=folium.Popup(popup_html, max_width=250),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=2
        ).add_to(m)

    st_folium(m, width="100%", height=420)

with col_rank:
    st.subheader("🏆 Ranking Quartieri")
    st.caption("Punteggio accumulato e ponderato nel tempo")
    
    sorted_districts = sorted(
        district_stats.items(), 
        key=lambda x: x[1]["total_score"], 
        reverse=True
    )
    
    if not sorted_districts:
        st.info("Nessun dato nel database.")
    else:
        for dist_name, stats in sorted_districts:
            score = stats["total_score"]
            badge = "🔴" if score >= 10 else ("🟡" if score >= 4 else "🟢")
            st.markdown(f"**{badge} {dist_name}**")
            st.progress(min(score / 20.0, 1.0))
            st.caption(f"Score Attivo: **{score}** | Reati: **{stats['news_count']}**")

st.write("---")

# 2. SEZIONE ANALYTICS & GRAFICI (FASE C)
st.subheader("📈 Visual Data Analytics")

if not all_news:
    st.info("Esegui aggiornamento per popolare i grafici di analisi.")
else:
    df = pd.DataFrame(all_news)

    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown("##### 🏷️ Distribuzione Reati per Categoria")
        cat_counts = df['category'].value_counts().reset_index()
        cat_counts.columns = ['Categoria', 'Conteggio']

        chart_cat = alt.Chart(cat_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('Categoria:N', sort='-y', title=None, axis=alt.Axis(labelAngle=-30)),
            y=alt.Y('Conteggio:Q', title="Numero Eventi"),
            color=alt.value("#ff4b4b")
        ).properties(height=280)

        st.altair_chart(chart_cat, use_container_width=True)

    with g_col2:
        st.markdown("##### 📍 Concentrazione Eventi per Quartiere")
        dist_counts = df['district'].value_counts().reset_index()
        dist_counts.columns = ['Quartiere', 'Conteggio']

        chart_dist = alt.Chart(dist_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('Quartiere:N', sort='-y', title=None, axis=alt.Axis(labelAngle=-30)),
            y=alt.Y('Conteggio:Q', title="Numero Eventi"),
            color=alt.value("#3182ce")
        ).properties(height=280)

        st.altair_chart(chart_dist, use_container_width=True)

st.write("---")

# 3. FEED STORICO
st.subheader("📡 Feed Storico Intelligence")
if not all_news:
    st.info("Il database è attualmente vuoto.")
else:
    for item in reversed(all_news):
        base_sev = item['severity']
        decayed_sev, days_ago = calculate_time_decay_severity(base_sev, item.get("published", ""))
        
        badge_color = "🔴" if decayed_sev >= 5 else ("🟡" if decayed_sev >= 2 else "🟢")
        header_text = f"{badge_color} [{item['district']}] {item['title']} ({days_ago} gg fa)"
        
        with st.expander(header_text):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**📍 Quartiere:** {item['district']}")
            with c2:
                st.write(f"**🏷️ Categoria:** {item['category']}")
            with c3:
                st.write(f"**⚠️ Severity (Oggi / Origine):** {decayed_sev} / {base_sev}")
            
            st.divider()
            st.write(f"**Sommario:** {item['summary']}")
            st.write(f"**Fonte:** {item['source']} | **Data:** {item['published']}")
            st.markdown(f"[Leggi articolo originale]({item['link']})")