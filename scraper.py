import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Fonti RSS locali di Pescara e Abruzzo
RSS_FEEDS = {
    "IlPescara": "https://www.ilpescara.it/rss/cronaca/",
    "Rete8": "https://www.rete8.it/feed/",
    # Possiamo aggiungere altre fonti con feed validi
}

def clean_html(raw_html):
    """Pulisce il testo rimuovendo tag HTML residui."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def fetch_latest_news(limit_per_feed=10):
    """
    Legge i feed RSS, estrae le notizie e restituisce una lista di dizionari con:
    - titolo
    - sommario / testo
    - fonte
    - link
    - data_pubblicazione
    """
    articles = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:limit_per_feed]:
                # Estrazione e pulizia campi
                title = entry.get("title", "")
                summary = clean_html(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "")
                published = entry.get("published", entry.get("updated", str(datetime.now())))

                articles.append({
                    "title": title,
                    "summary": summary,
                    "source": source_name,
                    "link": link,
                    "published": published
                })
        except Exception as e:
            print(f"[ERROR] Errore nel recupero feed per {source_name}: {e}")

    return articles

if __name__ == "__main__":
    # Test rapido di esecuzione locale
    print("🔎 Test Scraper Notizie Pescara...")
    news = fetch_latest_news(limit_per_feed=3)
    print(f"✅ Trovate {len(news)} notizie:\n")
    for idx, item in enumerate(news, 1):
        print(f"{idx}. [{item['source']}] {item['title']}")
        print(f"   URL: {item['link']}\n")