import re

# Comuni da escludere (Geofencing)
EXCLUDE_CITIES = [
    "montesilvano", "chieti", "l'aquila", "teramo", "sulmona", 
    "spoltore", "silvi", "pineto", "giulianova", "avezzano", "ortona", "penne"
]

# Blacklist per filtri di rumore (Sport, Spettacolo, Scienza/Meteo, Eventi)
NOISE_KEYWORDS = [
    "calcio", "partita", "serie a", "serie b", "serie c", "eccellenza", "gol", "rigore", 
    "allenatore", "squadra", "mercato", "piscina", "basket", "volley", "maratona", "torneo",
    "eclissi", "luna", "stelle", "meteo", "previsioni", "caldo", "ondata di calore",
    "concerto", "mostra", "sagra", "festa", "spettacolo", "teatro", "cinema", "oroscopo",
    "donare", "donazione", "avis", "fidas", "trasfusione", "carenza sangue"
]

# Whitelist di concetti legati a REATI / CRONACA NERA / SICUREZZA
CRIME_CONCEPTS = [
    "arresto", "arrestato", "arrestata", "arrestati", "fiancheggiatore",
    "furto", "rubato", "ladri", "spaccata", "scasso", "scippo", "rapina", "rapinato",
    "rissa", "aggressione", "pestaggio", "accoltellato", "ferito grave", "ferito",
    "spaccio", "droga", "cocaina", "eroina", "hashish", "pusher", "sequestro",
    "omicidio", "sparatoria", "morto", "cadavere", "sangue",
    "vandali", "vandalismo", "degrado", "incendio", "cassonetto a fuoco", "auto a fuoco",
    "incidente", "scontro", "investito", "investita", "tampone", "ribaltata",
    "carabinieri", "polizia", "questura", "guardia di finanza", "vigili del fuoco", "118"
]

# Mappatura Quartieri di Pescara
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
    "Colli": ["colli", "strada parco", "via di sotto", "via colle innamorati", "via rigopiano", "san giuseppe"],
    "Zanni": ["zanni", "via nausicaa", "borgo marino", "viale riviera"],
    "Tiburtina / Villa Redenta": ["tiburtina", "via aterno", "villa redenta", "via tirino"],
    "San Silvestro": ["san silvestro", "strada della bonifica", "san silvestro spiaggia"]
}

# Severità e Categorie
CRIME_KEYWORDS = {
    "Omicidio / Ferimento Grave": (10, ["omicidio", "sparatoria", "accoltellato", "ferito grave", "morto", "cadavere", "fucilata"]),
    "Rapina / Aggressione": (8, ["rapina", "aggressione", "scippo", "pestaggio", "rissa", "minacciato", "arrestato", "arresto"]),
    "Spaccio / Droga": (6, ["spaccio", "droga", "cocaina", "eroina", "pusher", "sequestro sostanze", "hashish"]),
    "Furto / Rattoppo": (5, ["furto", "rubato", "ladri", "spaccata", "topi d'appartamento", "auto rubata", "a fuoco", "incendio"]),
    "Atti Vandalici / Degrado": (3, ["vandali", "degrado", "schiamazzi", "danni", "incendio cassonetto"]),
    "Incidente Stradale": (4, ["incidente", "scontro", "investito", "ribaltata", "tampone", "investita"])
}

def is_pescara_news(text):
    """Filtro Geofencing."""
    text_lower = text.lower()
    for city in EXCLUDE_CITIES:
        if re.search(r'\b' + re.escape(city) + r'\b', text_lower):
            if "pescara" not in text_lower:
                return False
    return True

def is_crime_relevant(text):
    """
    Filtro tattico:
    1. Scarta se contiene concetti di rumore (sport, meteo, spettacoli)
    2. Accetta SOLO SE contiene almeno un concetto legato a reati o forze dell'ordine
    """
    text_lower = text.lower()
    
    # 1. Controllo Blacklist Rumore
    for noise_kw in NOISE_KEYWORDS:
        if re.search(r'\b' + re.escape(noise_kw) + r'\b', text_lower):
            return False

    # 2. Controllo Whitelist Reati / Sicurezza
    has_crime_concept = False
    for crime_kw in CRIME_CONCEPTS:
        if re.search(r'\b' + re.escape(crime_kw) + r'\b', text_lower):
            has_crime_concept = True
            break
            
    return has_crime_concept

def extract_location(text):
    """Estrae quartiere di Pescara."""
    text_lower = text.lower()
    for district, keywords in PEST_LOCATIONS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return district
    if "pescara" in text_lower:
        return "Centro"
    return None

def analyze_severity_and_category(text):
    """Assegna Categoria e Severity Index."""
    text_lower = text.lower()
    for category, (score, keywords) in CRIME_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return category, score
    return "Cronaca / Sicurezza", 3

def process_news_item(item):
    """Pipeline principale di analisi."""
    full_text = f"{item.get('title', '')} {item.get('summary', '')}"
    
    # 1. Filtro Geofencing (Solo Pescara)
    if not is_pescara_news(full_text):
        return None
        
    # 2. Filtro Tattico (Solo Reati/Sicurezza)
    if not is_crime_relevant(full_text):
        return None
        
    # 3. Estrazione Luogo
    district = extract_location(full_text)
    if not district:
        return None
        
    # 4. Calcolo Severity e Categoria
    category, severity = analyze_severity_and_category(full_text)
    
    item["district"] = district
    item["category"] = category
    item["severity"] = severity
    return item