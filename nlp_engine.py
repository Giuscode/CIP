import re

# Comuni da escludere tassativamente (Geofencing)
EXCLUDE_CITIES = [
    "montesilvano", "chieti", "l'aquila", "teramo", "sulmona", 
    "spoltore", "silvi", "pineto", "giulianova", "avezzano", "ortona", "penne"
]

# Parole chiave che indicano eventi sanitari/sociali (NON reati)
HEALTH_SOCIAL_KEYWORDS = [
    "donare", "donazione", "avis", "fidas", "trasfusione", 
    "carenza sangue", "raccolta sangue", "centro trasfusionale"
]

# Mappatura dettagliata delle vie e quartieri di Pescara Città
PEST_LOCATIONS = {
    "Rancitelli": ["rancitelli", "via tavo", "via ferrarese", "via lago di capestrano", "via lago di campotosto"],
    "Fontanelle": ["fontanelle", "via caduti per la liberta", "via fenice"],
    "Centro": [
        "corso umberto", "piazza salotto", "piazza della rinascita", "via firenze", 
        "via cesare battisti", "via nicola fabrizi", "via corso vittorio emanuele", "piazza della repubblica"
    ],
    "Pescara Vecchia": ["pescara vecchia", "corso manthonè", "via delle caserme", "piazza unione", "via bastioni"],
    "Portanuova": [
        "portanuova", "viale marconi", "via d'annunzio", "piazza garibaldi", 
        "stadio", "viale pindaro", "via del circuito", "viale colombo"
    ],
    "Colli": ["colli", "via di sotto", "via colle innamorati", "via rigopiano", "san giuseppe"],
    "Srada Parco": ["strada parco"],
    "Zanni": ["zanni", "via nausicaa", "borgo marino", "viale riviera"],
    "Tiburtina / Villa Redenta": ["tiburtina", "via aterno", "villa redenta", "via tirino"],
    "San Silvestro": ["san silvestro", "strada della bonifica", "san silvestro spiaggia"]
}

# Categorie reati e Severity
CRIME_KEYWORDS = {
    "Omicidio / Ferimento Grave": (10, ["omicidio", "sparatoria", "accoltellato", "ferito grave", "sangue", "morto", "fucilata"]),
    "Rapina / Aggressione": (8, ["rapina", "aggressione", "scippo", "pestaggio", "rissa", "minacciato", "arrestato", "arresto"]),
    "Spaccio / Droga": (6, ["spaccio", "droga", "cocaina", "eroina", "pusher", "sequestro sostanze", "hashish"]),
    "Furto / Rattoppo": (5, ["furto", "rubato", "ladri", "spaccata", "topi d'appartamento", "auto rubata", "a fuoco", "incendio"]),
    "Atti Vandalici / Degrado": (3, ["vandali", "degrado", "schiamazzi", "danni", "incendio cassonetto"]),
    "Incidente Stradale": (4, ["incidente", "scontro", "investito", "ribaltata", "tampone", "investita"])
}

def is_pescara_news(text):
    """Verifica che la notizia non parli esplicitamente di altre città abruzzesi."""
    text_lower = text.lower()
    for city in EXCLUDE_CITIES:
        if re.search(r'\b' + re.escape(city) + r'\b', text_lower):
            # Se cita Montesilvano/Chieti ma NON cita esplicitamente Pescara, la escludiamo
            if "pescara" not in text_lower:
                return False
    return True

def is_health_or_social_news(text):
    """Filtra notizie sanitarie/sociali (es. donazione sangue)."""
    text_lower = text.lower()
    for kw in HEALTH_SOCIAL_KEYWORDS:
        if kw in text_lower:
            return True
    return False

def extract_location(text):
    """Identifica il quartiere specifico di Pescara."""
    text_lower = text.lower()
    for district, keywords in PEST_LOCATIONS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return district
            
            
    if "pescara" in text_lower:
        return "Centro"
    return None

def analyze_severity_and_category(text):
    """Calcola Severity Index ignorando falsi positivi sanitari."""
    text_lower = text.lower()
    
    # Se la notizia è medica/sanitaria (es. Avis, donazioni), la classifichiamo come notizia di servizio a bassissima severità
    if is_health_or_social_news(text):
        return "Servizio / Sanità", 1

    for category, (score, keywords) in CRIME_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return category, score
    return "Cronaca Generica", 2

def process_news_item(item):
    """Elabora e filtra la notizia."""
    full_text = f"{item.get('title', '')} {item.get('summary', '')}"
    
    # Filtro Geofencing
    if not is_pescara_news(full_text):
        return None
        
    district = extract_location(full_text)
    if not district:
        return None
        
    category, severity = analyze_severity_and_category(full_text)
    
    item["district"] = district
    item["category"] = category
    item["severity"] = severity
    return item