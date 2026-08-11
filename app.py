import streamlit as st

# Configurazione della pagina "Palantir Style"
st.set_page_config(
    page_title="C.I.P - Crime Index Pescara",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo Dashboard
st.title("C.I.P.: Crime Index Pescara")
st.caption("Sistema iperlocale di monitoraggio e analisi notizie di cronaca")

st.divider()

# Metric Card temporanea
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Status Sistema", value="Online", delta="OK")
with col2:
    st.metric(label="Notizie Ingestite", value="0", delta="In attesa Scraper")
with col3:
    st.metric(label="Crime Index Medio", value="0.0", delta="0.0%")

st.info("⚠️ Dashboard in fase di inizializzazione. In attesa dei dati")
