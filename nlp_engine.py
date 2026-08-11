import re

# Database di parole chiave per la geolocalizzazione sui quartieri/zone di Pescara
PEST_LOCATIONS = {
    "Rancitelli": ["rancitelli", "via tavo", "ferrarese"],
    "Fontanelle": ["fontanelle", "via caduti per la liberta"],
    "Centro": ["corso umberto", "piazza salotto", "piazza della rinascita", "via firenze", "via cesare battisti", "centro", "piazza santa caterina", ],
    "Pescara Vecchia": ["pescara vecchia", "corso manthonè", "via delle caserme", "piazza unione"],
    "Portanuova": ["portanuova", "viale marconi", "via d'annunzio", "piazza garibaldi", "stadio", "viale pindaro"],
    "Colli": ["colli", "via di sotto", "via colle innamorati"],
    "Strada Parco": ["strada parco"],
    "Zanni": ["zanni", "via nausicaa", "borgo marino"],
    "Tiburtina / Villa Redenta": ["tiburtina", "via aterno", "villa redenta"],
    "San Silvestro": ["san silvestro", "strada della bonifica"]
}

# Parole chiave e relativi punteggi di gravità (Severity Score 1-10)
CRIME_KEYWORDS = {
    "Omicidio / Ferimento Grave": (10, ["omicidio", "sparatoria", "accoltellato", "ferito grave", "sangue", "morto"]),
    "Rapina / Aggressione": (8, ["rapina", "aggressione", "scippo", "pestaggio", "rissa", "minacciato"]),
    "Spaccio / Droga": (6, ["spaccio", "droga", "cocaina", "eroina", "pusher", "sequestro sostanze"]),
    "Furto / Rattoppo": (5, ["furto", "rubato", "ladri", "spaccata", "topi d'appartamento", "auto rubata"]),
    "Atti Vandalici / Degrado": (3, ["vandali", "degrado", "schiamazzi", "danni", "incendio cassonetto"]),
    "Incidente Stradale": (4, ["incidente", "scontro", "investito", "ribaltata", "tampone"])
}

def extract_location(text):
    """Identifica il quartiere di Pescara menzionato nel testo."""
    text_lower = text.lower()
    for district, keywords in PEST_LOCATIONS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return district
    return "Pescara (Generico)"

def analyze_severity_and_category(text):
    """Classifica la notizia e assegna uno score di gravità (1-10)."""
    text_lower = text.lower()
    for category, (score, keywords) in CRIME_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return category, score
    return "Cronaca Generica", 2

def process_news_item(item):
    """Arricchisce il dizionario della notizia con location, categoria e severity."""
    full_text = f"{item.get('title', '')} {item.get('summary', '')}"
    
    district = extract_location(full_text)
    category, severity = analyze_severity_and_category(full_text)
    
    item["district"] = district
    item["category"] = category
    item["severity"] = severity
    return item

if __name__ == "__main__":
    # Test di verifica locale
    sample_text = "Pescara: ferito grave in via Aterno, arrestato un 66enne per aggressione"
    print("🧪 Test Engine NLP su notizia di esempio:")
    print(f"Testo: '{sample_text}'")
    
    dummy_item = {"title": sample_text, "summary": ""}
    processed = process_news_item(dummy_item)
    
    print(f"📍 Quartiere Rilevato: {processed['district']}")
    print(f"🏷️ Categoria: {processed['category']}")
    print(f"⚠️ Severity Index: {processed['severity']}/10")