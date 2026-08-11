import streamlit as st
from scraper import fetch_latest_news
from nlp_engine import process_news_item

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

# Sidebar per i controlli
st.sidebar.header("⚙️ Pannello di Controllo")
limit = st.sidebar.slider("Numero notizie per fonte:", min_value=1, max_value=20, value=5)
st.sidebar.divider()
st.sidebar.info("Modulo 1 (RSS) & Modulo 2 (NLP) Attivi.")

# Fetch e processing delle notizie
with st.spinner("Analisi semantica e geolocalizzazione in corso..."):
    raw_news = fetch_latest_news(limit_per_feed=limit)
    processed_news = [process_news_item(item) for item in raw_news]

# Calcolo Metriche Generali
total_news = len(processed_news)
if total_news > 0:
    avg_severity = sum(item["severity"] for item in processed_news) / total_news
else:
    avg_severity = 0.0

# Metric Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Status Sistema", value="Online", delta="Scraper + NLP Active")
with col2:
    st.metric(label="Notizie Ingestite", value=total_news, delta=f"{total_news} elaborate")
with col3:
    st.metric(
        label="Severity Index Medio", 
        value=f"{avg_severity:.1f} / 10", 
        delta="Livello Allerta" if avg_severity > 5 else "Nella Norma",
        delta_color="inverse" if avg_severity > 5 else "normal"
    )

st.write("---")

# Visualizzazione Feed Notizie Processate
st.subheader("📡 Feed Intelligence Cronaca Locale")

if not processed_news:
    st.warning("Nessuna notizia trovata al momento.")
else:
    for idx, item in enumerate(processed_news, 1):
        # Selezione colore in base alla severità
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
