import math
from datetime import datetime, timezone

# Decadimento temporale (lambda): 0.15 = dimezza il peso in ~4.6 giorni
DECAY_LAMBDA = 0.15

def parse_date(date_str):
    """Tenta di convertire diverse stringhe di data nel formato datetime."""
    if not date_str:
        return datetime.now(timezone.utc)
    
    # Prova formati comuni nei feed RSS (es. RFC 822 / ISO)
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass
            
    # Fallback se la data non è parsabile
    return datetime.now(timezone.utc)

def calculate_time_decay_severity(base_severity, published_date_str):
    """Calcola la severità attualizzata in base ai giorni trascorsi."""
    pub_date = parse_date(published_date_str)
    now = datetime.now(timezone.utc)
    
    # Tempo trascorso in giorni
    delta_days = (now - pub_date).total_seconds() / 86400.0
    if delta_days < 0:
        delta_days = 0

    # Formula del decadimento esponenziale
    decayed_severity = base_severity * math.exp(-DECAY_LAMBDA * delta_days)
    return round(decayed_severity, 2), round(delta_days, 1)

def compute_district_crime_index(all_news):
    """
    Raggruppa le notizie per quartiere e calcola:
    - Index totale attualizzato del quartiere
    - Numero reati
    - Notizia più recente
    """
    district_data = {}
    
    for item in all_news:
        district = item.get("district", "Centro")
        base_sev = item.get("severity", 2)
        pub_date = item.get("published", "")
        
        decayed_sev, days_ago = calculate_time_decay_severity(base_sev, pub_date)
        
        if district not in district_data:
            district_data[district] = {
                "total_score": 0.0,
                "news_count": 0,
                "max_severity": 0,
                "items": []
            }
            
        district_data[district]["total_score"] += decayed_sev
        district_data[district]["news_count"] += 1
        district_data[district]["items"].append(item)
        
        if base_sev > district_data[district]["max_severity"]:
            district_data[district]["max_severity"] = base_sev

    # Arrotondiamo i punteggi
    for d in district_data:
        district_data[d]["total_score"] = round(district_data[d]["total_score"], 1)

    return district_data