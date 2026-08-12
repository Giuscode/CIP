import streamlit as st
import folium
from streamlit_folium import st_folium

from scraper import fetch_latest_news
from nlp_engine import process_news_item
from db_manager import sync_news_with_db, load_database

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

# Tasto per forzare l'ingestione
if st.sidebar.button("🔄 Aggiorna Notizie"):
    with st.spinner("Scraping e analisi in corso..."):
        raw_news = fetch_latest_news(limit_per_feed=limit)
        processed = [process_news_item(item) for item in raw_news]
        clean_news = [item for item in processed if item is not None]
        
        # Sincronizza col DB
        _, added = sync_news_with_db(clean_news)
        st.sidebar.success(f"Aggiunte {added} nuove notizie al DB!")

# Carica l'intero database storico
all_news = load_database()

# Metriche Generali
total_news = len(all_news)
avg_severity = sum(item["severity"] for item in all_news) / total_news if total_news > 0 else 0.0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Status Sistema", value="Online", delta="DB Persistente Attivo")
with col2:
    st.metric(label="Notizie nel Database", value=total_news, delta=f"{total_news} storiche")
with col3:
    st.metric(
        label="Severity Index Medio", 
        value=f"{avg_severity:.1f} / 10", 
        delta="Livello Allerta" if avg_severity > 5 else "Nella Norma",
        delta_color="inverse" if avg_severity > 5 else "normal"
    )

st.write("---")

# Mappa Geospaziale
st.subheader("🗺️ Mappa Storica Reati & Eventi")

m = folium.Map(location=[42.4643, 14.2142], zoom_start=13, tiles="CartoDB dark_matter")

for item in all_news:
    district = item.get("district", "Centro")
    coords = DISTRICT_COORDS.get(district, DISTRICT_COORDS["Centro"])
    severity = item.get("severity", 2)
    color = "#ff4b4b" if severity >= 7 else ("#faca15" if severity >= 4 else "#3182ce")
    
    popup_html = f"""
    <div style='font-family: sans-serif; width: 220px;'>
        <h4 style='margin-bottom:5px;'>{district}</h4>
        <p><b>Categoria:</b> {item['category']}</p>
        <p><b>Severity:</b> <span style='color:{color}; font-weight:bold;'>{severity}/10</span></p>
        <p style='font-size:12px;'>{item['title']}</p>
        <a href='{item['link']}' target='_blank'>Leggi articolo</a>
    </div>
    """
    
    folium.CircleMarker(
        location=coords,
        radius=8 + (severity * 1.5),
        popup=folium.Popup(popup_html, max_width=250),
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.6,
        weight=2
    ).add_to(m)

st_folium(m, width="100%", height=450)

st.write("---")

# Feed Notizie da DB
st.subheader("📡 Feed Storico Intelligence")

if not all_news:
    st.info("Il database è attualmente vuoto. Clicca su '🔄 Esegui Ingestione Notizie' nella sidebar per iniziare.")
else:
    for item in reversed(all_news):  # Dalla più recente alla più vecchia
        sev = item['severity']
        badge_color = "🔴" if sev >= 7 else ("🟡" if sev >= 4 else "🟢")
        header_text = f"{badge_color} [{item['district']}] {item['title']}"
        
        with st.expander(header_text):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**📍 Quartiere:** {item['district']}")
            with c2:
                st.write(f"**🏷️ Categoria:** {item['category']}")
            with c3:
                st.write(f"**⚠️ Severity Score:** {item['severity']}/10")
            
            st.divider()
            st.write(f"**Sommario:** {item['summary']}")
            st.write(f"**Fonte:** {item['source']} | **Data:** {item['published']}")
            st.markdown(f"[Leggi articolo originale]({item['link']})")
