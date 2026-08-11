import streamlit as st
from scraper import fetch_latest_news

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
st.sidebar.info("Modulo 1: Ingestione Dati (RSS) attivo.")

# Tasto per aggiornare manualmente i dati
if st.button("🔄  Notizie in Tempo Reale"):
    st.cache_data.clear()

# Fetch delle notizie usando lo scraper
with st.spinner("Connessione alle fonti di cronaca di Pescara in corso..."):
    news_data = fetch_latest_news(limit_per_feed=limit)

# Metric Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Status Sistema", value="Online", delta="Scraper Attivo")
with col2:
    st.metric(label="Notizie Ingestite", value=len(news_data), delta=f"{len(news_data)} recenti")
with col3:
    st.metric(label="Fonti Monitorate", value="2", delta="Rete8, IlPescara")

st.write("---")

# Visualizzazione Feed Notizie Ingestite
st.subheader("📡 Feed  Cronaca Locale")

if not news_data:
    st.warning("Nessuna notizia trovata al momento.")
else:
    for idx, item in enumerate(news_data, 1):
        with st.expander(f"[{item['source']}] {item['title']}"):
            st.write(f"**Data:** {item['published']}")
            st.write(f"**Sommario:** {item['summary']}")
            st.markdown(f"[Leggi articolo originale]({item['link']})")
